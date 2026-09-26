from dataclasses import dataclass

from django.conf import settings
from django.db.models import F, Q

from rest_framework.exceptions import ValidationError

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.vault import (
    VAULT_BACKEND_REDIS,
    MaskTokenVaultUnavailable,
    get_mask_token_vault,
    load_active_fingerprint_key,
    mask_token_vault_backend,
)
from jadawel.core.mcp.models import MCPEndpoint


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

    Checks exactly what ``mask_table_rows`` needs: a vault with room for
    a full batch (for Redis also bounded and ``noeviction``, with memory
    headroom), and the active fingerprint key. Runs regardless of whether any
    policy is non-empty, so admission can refuse to create a protection policy
    that every read would reject.
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
    if not vault.is_ready():
        return MCPProtectionReadiness(
            False,
            MCPProtectionSafeReason.PROTECTION_REDIS_UNAVAILABLE
            if vault.backend == VAULT_BACKEND_REDIS
            else MCPProtectionSafeReason.PROTECTION_VAULT_UNAVAILABLE,
        )

    try:
        load_active_fingerprint_key()
    except MaskTokenVaultUnavailable:
        return MCPProtectionReadiness(
            False, MCPProtectionSafeReason.PROTECTION_KEY_UNAVAILABLE
        )

    return MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)


MCP_PROTECTION_STAFF_FLAG = "mcp-protected-fields-staff"
MCP_PROTECTION_FLAG = "mcp-protected-fields"


def ensure_policy_admission_allowed(user) -> None:
    """Gate policy admission without ever weakening enforcement.

    Every owner may protect fields: the vault needs no setup and
    ``ensure_protection_vault_ready`` refuses admission when it is not ready.
    ``mcp-protected-fields-staff`` alone restricts admission to staff for a
    staged rollout; ``mcp-protected-fields`` (or ``*``) lifts that restriction
    and is otherwise no longer needed.
    """

    configured_flags = settings.FEATURE_FLAGS
    if isinstance(configured_flags, str):
        configured_flags = (configured_flags,)
    flags = {str(flag).strip().lower() for flag in configured_flags}
    if "*" in flags or MCP_PROTECTION_FLAG in flags:
        return
    if MCP_PROTECTION_STAFF_FLAG not in flags or user.is_staff:
        return
    raise ValidationError(
        {
            "protected_field_ids": (
                "MCP protected-field policies are not enabled for this account."
            )
        }
    )


class MCPProtectionVaultNotReady(Exception):
    """Protecting a field now would leave every read of its table blocked."""

    def __init__(self, safe_reason_code: str):
        super().__init__(safe_reason_code)
        self.safe_reason_code = safe_reason_code


def ensure_protection_vault_ready() -> None:
    """Refuse to protect a new field while protected reads would fail closed.

    Enforcement never depends on this check: a policy saved before an outage
    still blocks reads. It only stops an owner from creating an endpoint whose
    protected tables are unreadable from the start. Removing protection is never
    gated, so an owner can always recover during an outage.
    """

    readiness = check_mask_token_vault_readiness()
    if not readiness.ready:
        raise MCPProtectionVaultNotReady(readiness.safe_reason_code)
