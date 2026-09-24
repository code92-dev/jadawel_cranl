import logging
import secrets
import time
from dataclasses import dataclass

from django.db import DatabaseError
from django.db.models import F, Q

from redis.exceptions import RedisError

from arabase.mcp.protection.egress import MAX_ISSUED_OR_REDEEMED_PER_CALL
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.vault import (
    MASK_TOKEN_EXPIRY_INDEX,
    MAX_GLOBAL_TOKENS,
    VAULT_BACKEND_REDIS,
    DatabaseMaskTokenVault,
    MaskTokenVaultUnavailable,
    _load_active_fingerprint_key,
    get_mask_token_vault,
    mask_token_vault_backend,
)
from jadawel.core.mcp.models import MCPEndpoint

logger = logging.getLogger(__name__)

READINESS_OPERATION_TIMEOUT_SECONDS = 0.5


@dataclass(frozen=True, slots=True)
class MCPProtectionReadiness:
    ready: bool
    safe_reason_code: str


def check_mcp_protection_policy_readiness() -> MCPProtectionReadiness:
    """Prove the durable endpoint-policy invariants without reading cell data."""

    endpoint_count = MCPEndpoint.objects.count()
    policy_count = MCPProtectionPolicy.objects.count()
    if endpoint_count != policy_count:
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.POLICY_COUNT_MISMATCH
        )

    invalid_policy_exists = MCPProtectionPolicy.objects.filter(
        Q(revision__lt=1)
        | Q(access_generation__lt=1)
        | ~Q(lifecycle_status__in=MCPProtectionLifecycleStatus.values)
        | Q(
            lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
            safe_reason_code__gt="",
        )
        | (
            ~Q(lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE)
            & Q(safe_reason_code="")
        )
    ).exists()
    if invalid_policy_exists:
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.POLICY_STATE_INVALID
        )

    invalid_relation_exists = (
        MCPProtectedField.objects.annotate(
            endpoint_workspace_id=F("policy__endpoint__workspace_id"),
            field_workspace_id=F("field__table__database__workspace_id"),
        )
        .filter(
            ~Q(state__in=MCPProtectedFieldState.values)
            | Q(state=MCPProtectedFieldState.ACTIVE, safe_reason_code__gt="")
            | Q(state=MCPProtectedFieldState.SUSPENDED, safe_reason_code="")
            | Q(field__trashed=True)
            | Q(field__table__trashed=True)
            | Q(field__table__database__trashed=True)
            | ~Q(endpoint_workspace_id=F("field_workspace_id"))
        )
        .exists()
    )
    if invalid_relation_exists:
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.POLICY_RELATION_INVALID
        )

    if MCPProtectedField.objects.filter(
        state=MCPProtectedFieldState.ACTIVE,
        policy__lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
    ).exists():
        vault_readiness = check_mask_token_vault_readiness()
        if not vault_readiness.ready:
            return vault_readiness

    return MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)


def check_mask_token_vault_readiness() -> MCPProtectionReadiness:
    """Prove that a protected read could issue mask tokens right now.

    Checks exactly what ``mask_direct_row_output`` needs: a vault with room for
    a full batch (for Redis also bounded and ``noeviction``, with memory
    headroom), and the active fingerprint key. Runs regardless of whether any policy is non-empty, so admission can refuse to
    create a protection policy that every read would reject.
    """

    try:
        vault = get_mask_token_vault()
    except MaskTokenVaultUnavailable:
        # Redis was selected but cannot be configured (for example, no URL), or
        # the backend name is unknown.
        return MCPProtectionReadiness(
            False,
            MCPProtectionSafeReason.PROTECTION_REDIS_UNAVAILABLE
            if mask_token_vault_backend() == VAULT_BACKEND_REDIS
            else MCPProtectionSafeReason.PROTECTION_VAULT_UNAVAILABLE,
        )
    if isinstance(vault, DatabaseMaskTokenVault):
        vault_readiness = _check_database_vault(vault)
    else:
        vault_readiness = _check_redis_vault(vault)
    if not vault_readiness.ready:
        return vault_readiness

    try:
        _load_active_fingerprint_key()
    except MaskTokenVaultUnavailable:
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.PROTECTION_KEY_UNAVAILABLE
        )

    return MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)


def _check_database_vault(vault: DatabaseMaskTokenVault) -> MCPProtectionReadiness:
    """The table is reachable and has room for one more full batch."""

    try:
        started = time.monotonic()
        live_tokens = vault.live_token_count()
        if live_tokens + MAX_ISSUED_OR_REDEEMED_PER_CALL >= MAX_GLOBAL_TOKENS:
            raise MaskTokenVaultUnavailable
        if time.monotonic() - started > READINESS_OPERATION_TIMEOUT_SECONDS:
            raise MaskTokenVaultUnavailable
    except (MaskTokenVaultUnavailable, DatabaseError):
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.PROTECTION_VAULT_UNAVAILABLE
        )
    return MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)


def _check_redis_vault(vault) -> MCPProtectionReadiness:
    try:
        redis = vault.redis
        started = time.monotonic()
        redis.ping()
        config_get = getattr(redis, "config_get", None)
        if config_get is None:
            raise RedisError("Redis configuration cannot be verified")
        memory = config_get("maxmemory")
        policy = config_get("maxmemory-policy")
        maxmemory = int(memory.get("maxmemory", 0))
        if maxmemory <= 0 or policy.get("maxmemory-policy") != "noeviction":
            raise RedisError("Redis is not a bounded noeviction vault")
        info = redis.info("memory")
        used_memory = int(info.get("used_memory", 0))
        memory_ratio = used_memory / maxmemory
        if memory_ratio >= 0.70:
            logger.error("MCP protection Redis memory alert: %.3f used", memory_ratio)
        if memory_ratio >= 0.60:
            raise RedisError("Redis memory headroom is below the safety floor")
        canary_key = f"jadawel:mcp-protection:readiness:{secrets.token_hex(8)}"
        if not redis.set(canary_key, "1", ex=5, nx=True):
            raise RedisError("Redis readiness canary could not be written")
        canary_ttl = redis.ttl(canary_key)
        if canary_ttl <= 0:
            raise RedisError("Redis readiness canary did not receive a TTL")
        if redis.get(canary_key) not in ("1", b"1"):
            raise RedisError("Redis readiness canary could not be read")
        redis.delete(canary_key)
        live_tokens = int(redis.zcard(MASK_TOKEN_EXPIRY_INDEX))
        if live_tokens + MAX_ISSUED_OR_REDEEMED_PER_CALL >= MAX_GLOBAL_TOKENS:
            raise RedisError("Redis token reservation headroom is exhausted")
        if time.monotonic() - started > READINESS_OPERATION_TIMEOUT_SECONDS:
            raise RedisError("Redis readiness exceeded its bounded timeout")
    except (MaskTokenVaultUnavailable, RedisError, OSError, ValueError, TypeError):
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.PROTECTION_REDIS_UNAVAILABLE
        )

    return MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)
