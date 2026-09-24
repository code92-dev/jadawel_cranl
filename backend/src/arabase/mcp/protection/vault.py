import base64
import hashlib
import hmac
import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.utils.crypto import salted_hmac

from redis import Redis
from redis.exceptions import RedisError

from arabase.mcp.protection.canonical import (
    CANONICAL_VALUE_VERSION,
    canonicalize_typed_value,
)
from arabase.mcp.protection.tokens import GeneratedMaskToken, generate_mask_token

MASK_TOKEN_TTL_SECONDS = 24 * 60 * 60
MASK_TOKEN_REDIS_PREFIX = "jadawel:mcp-protection:v1:"
MASK_TOKEN_EXPIRY_INDEX = f"{MASK_TOKEN_REDIS_PREFIX}expiry"
MASK_TOKEN_ENDPOINT_INDEX_PREFIX = f"{MASK_TOKEN_REDIS_PREFIX}endpoint:"
MAX_ISSUANCE_MEMORY_RATIO = 0.60
MAX_ENDPOINT_TOKENS = 10_000
MAX_GLOBAL_TOKENS = 50_000
DERIVED_FINGERPRINT_KEY_ID = "secret-derived-v1"
DERIVED_FINGERPRINT_KEY_SALT = "jadawel.mcp-protection.fingerprint-key.v1"
VAULT_BACKEND_DATABASE = "database"
VAULT_BACKEND_REDIS = "redis"
PURGE_BATCH_SIZE = 500
# PostgreSQL advisory-lock keys for database-vault issuer admission, in a
# namespace no other Jadawel code uses (0x4A4D5043, "JMPC").
_ISSUER_GLOBAL_LOCK_BASE = 0x4A4D5043 << 32
_ISSUER_ENDPOINT_LOCK_BASE = 0x4A4D5044 << 32

_RESERVE_TOKEN_BATCH_SCRIPT = """
local now = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)
local item_count = tonumber(ARGV[1])
if redis.call('ZCARD', KEYS[1]) + item_count > tonumber(ARGV[3]) then
  return -1
end
if redis.call('ZCARD', KEYS[2]) + item_count > tonumber(ARGV[4]) then
  return -1
end
local existing = redis.call('MGET', unpack(KEYS, 3, #KEYS))
for item_index = 1, item_count do
  if existing[item_index] then
    return 0
  end
end
local zadd_arguments = {}
for item_index = 1, item_count do
  local argument_index = 5 + ((item_index - 1) * 3)
  local expires_at = ARGV[argument_index]
  local digest = ARGV[argument_index + 1]
  local record = ARGV[argument_index + 2]
  redis.call('SET', KEYS[item_index + 2], record, 'EX', ARGV[2])
  table.insert(zadd_arguments, expires_at)
  table.insert(zadd_arguments, digest)
end
redis.call('ZADD', KEYS[1], unpack(zadd_arguments))
redis.call('ZADD', KEYS[2], unpack(zadd_arguments))
return item_count
"""


class MaskTokenVaultUnavailable(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MaskTokenBinding:
    endpoint_id: int
    workspace_id: int
    table_id: int
    row_id: int
    field_id: int
    policy_revision: int
    access_generation: int
    operation_class: str
    observed_row_state: str
    field_type: str


@dataclass(frozen=True, slots=True)
class IssuedMaskToken:
    raw_handle: str
    digest: str
    envelope: dict


def _explicit_keyring_configured() -> bool:
    return bool(
        settings.MCP_PROTECTION_FINGERPRINT_KEYS
        or settings.MCP_PROTECTION_ACTIVE_KEY_ID
    )


def _derived_fingerprint_key() -> bytes:
    """A dedicated key for installs that configure no keyring.

    Derived with a fixed salt, so it is independent of every other use of
    ``SECRET_KEY``, identical in every process and replica, and never written to
    the database next to the fingerprints it protects. Rotating ``SECRET_KEY``
    rotates it, which safely revokes every outstanding token.
    """

    secret = getattr(settings, "SECRET_KEY", "")
    if not secret:
        raise MaskTokenVaultUnavailable
    return salted_hmac(
        DERIVED_FINGERPRINT_KEY_SALT, "fingerprint", secret=secret, algorithm="sha256"
    ).digest()


def _decode_configured_key(encoded_key) -> bytes:
    if not encoded_key:
        raise MaskTokenVaultUnavailable
    try:
        key = base64.b64decode(encoded_key, validate=True)
    except (ValueError, TypeError) as exc:
        raise MaskTokenVaultUnavailable from exc
    if len(key) != 32:
        raise MaskTokenVaultUnavailable
    return key


def _load_active_fingerprint_key() -> tuple[str, bytes]:
    if not _explicit_keyring_configured():
        return DERIVED_FINGERPRINT_KEY_ID, _derived_fingerprint_key()
    key_id = settings.MCP_PROTECTION_ACTIVE_KEY_ID
    return key_id, _decode_configured_key(
        settings.MCP_PROTECTION_FINGERPRINT_KEYS.get(key_id)
    )


def _load_fingerprint_key(key_id: str) -> bytes:
    # Configuring an explicit keyring retires the derived key, which revokes
    # the tokens it issued instead of keeping two authorities alive.
    if not _explicit_keyring_configured():
        if key_id != DERIVED_FINGERPRINT_KEY_ID:
            raise MaskTokenVaultUnavailable
        return _derived_fingerprint_key()
    return _decode_configured_key(settings.MCP_PROTECTION_FINGERPRINT_KEYS.get(key_id))


def _build_token_records(
    items: list[tuple["MaskTokenBinding", Any]],
) -> tuple[datetime, list[tuple[GeneratedMaskToken, dict]]]:
    """Generate one fresh token and its binding record per protected value."""

    key_id, fingerprint_key = _load_active_fingerprint_key()
    expires_at = datetime.now(UTC) + timedelta(seconds=MASK_TOKEN_TTL_SECONDS)
    generated: list[tuple[GeneratedMaskToken, dict]] = []
    for binding, value in items:
        canonical_value = canonicalize_typed_value(binding.field_type, value)
        fingerprint = hmac.new(
            fingerprint_key, canonical_value, hashlib.sha256
        ).hexdigest()
        generated.append(
            (
                generate_mask_token(),
                {
                    **asdict(binding),
                    "canonicalization_version": CANONICAL_VALUE_VERSION,
                    "expires_at": expires_at.isoformat(),
                    "fingerprint_key_id": key_id,
                    "value_fingerprint": fingerprint,
                },
            )
        )
    digests = [token.digest for token, _record in generated]
    if len(set(digests)) != len(digests):
        raise MaskTokenVaultUnavailable
    return expires_at, generated


def _record_matches(record: dict, binding: "MaskTokenBinding", current_value) -> bool:
    """Check a stored record against the cell it is being redeemed for."""

    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
        if expires_at <= datetime.now(UTC):
            return False
        expected = asdict(binding)
        if any(record.get(key) != value for key, value in expected.items()):
            return False
        if record.get("canonicalization_version") != CANONICAL_VALUE_VERSION:
            return False
        fingerprint_key = _load_fingerprint_key(record["fingerprint_key_id"])
        canonical_value = canonicalize_typed_value(binding.field_type, current_value)
        fingerprint = hmac.new(
            fingerprint_key, canonical_value, hashlib.sha256
        ).hexdigest()
    except (
        KeyError,
        AttributeError,
        TypeError,
        ValueError,
        OverflowError,
        UnicodeEncodeError,
        MaskTokenVaultUnavailable,
    ):
        return False
    return hmac.compare_digest(record.get("value_fingerprint", ""), fingerprint)


class RedisMaskTokenVault:
    """Digest-addressed Redis vault which never persists the token or value."""

    def __init__(self, redis_client: Redis | None = None):
        self._enforce_memory_headroom = redis_client is None
        if redis_client is not None:
            self.redis = redis_client
            return
        redis_url = settings.MCP_PROTECTION_REDIS_URL
        if not redis_url and settings.MCP_PROTECTION_ALLOW_SHARED_REDIS:
            redis_url = settings.REDIS_URL
        if not redis_url:
            raise MaskTokenVaultUnavailable
        try:
            self.redis = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.5,
            )
        except (TypeError, ValueError) as exc:
            raise MaskTokenVaultUnavailable from exc

    def issue(self, binding: MaskTokenBinding, value: Any) -> IssuedMaskToken:
        return self.issue_many([(binding, value)])[0]

    def issue_many(
        self, items: list[tuple[MaskTokenBinding, Any]]
    ) -> list[IssuedMaskToken]:
        """Issue one endpoint's tokens with one atomic Redis script."""

        if not items:
            return []
        endpoint_id = items[0][0].endpoint_id
        if any(binding.endpoint_id != endpoint_id for binding, _value in items):
            raise MaskTokenVaultUnavailable
        self._ensure_issuance_headroom()
        expires_at, built = _build_token_records(items)
        generated = [
            (token, json.dumps(record, separators=(",", ":"), sort_keys=True))
            for token, record in built
        ]
        digests = [token.digest for token, _record in generated]
        try:
            result = self.redis.register_script(_RESERVE_TOKEN_BATCH_SCRIPT)(
                keys=[
                    MASK_TOKEN_EXPIRY_INDEX,
                    f"{MASK_TOKEN_ENDPOINT_INDEX_PREFIX}{endpoint_id}",
                    *[f"{MASK_TOKEN_REDIS_PREFIX}{digest}" for digest in digests],
                ],
                args=[
                    len(generated),
                    MASK_TOKEN_TTL_SECONDS,
                    MAX_GLOBAL_TOKENS,
                    MAX_ENDPOINT_TOKENS,
                    *[
                        argument
                        for token, record in generated
                        for argument in (
                            # Keep the reservation at least as long as the Redis TTL;
                            # flooring a fractional Unix timestamp could release it
                            # early.
                            int(expires_at.timestamp()) + 1,
                            token.digest,
                            record,
                        )
                    ],
                ],
            )
        except RedisError as exc:
            raise MaskTokenVaultUnavailable from exc
        if result != len(generated):
            raise MaskTokenVaultUnavailable
        return [_issued(token) for token, _record in generated]

    def _ensure_issuance_headroom(self) -> None:
        """Stop new issuance before the dedicated vault reaches its safety floor.

        Test fakes and explicitly injected Redis clients are deliberately exempt:
        production clients are always constructed from the configured URL and
        therefore get the bounded configuration check on every issuance batch.
        """

        if not self._enforce_memory_headroom:
            return
        try:
            config_get = getattr(self.redis, "config_get", None)
            if config_get is None:
                raise RedisError("Redis configuration cannot be verified")
            memory = config_get("maxmemory")
            policy = config_get("maxmemory-policy")
            maxmemory = int(memory.get("maxmemory", 0))
            if maxmemory <= 0 or policy.get("maxmemory-policy") != "noeviction":
                raise RedisError("Redis is not a bounded noeviction vault")
            used_memory = int(self.redis.info("memory").get("used_memory", 0))
            if used_memory / maxmemory >= MAX_ISSUANCE_MEMORY_RATIO:
                raise RedisError("Redis memory headroom is below the safety floor")
        except (RedisError, OSError, ValueError, TypeError, AttributeError) as exc:
            raise MaskTokenVaultUnavailable from exc

    def redeem(
        self, raw_handle: str, binding: MaskTokenBinding, current_value: Any
    ) -> bool:
        """Validate a same-cell token against its current row state.

        A successful redemption is intentionally non-consuming: retries of an
        idempotent MCP request must preserve the same cell while the token remains
        valid.  Redis contains only the binding and a keyed fingerprint, never the
        raw value or handle.
        """

        try:
            digest = hashlib.sha256(raw_handle.encode("ascii")).hexdigest()
            stored = self.redis.get(f"{MASK_TOKEN_REDIS_PREFIX}{digest}")
        except (AttributeError, TypeError, UnicodeEncodeError):
            return False
        except RedisError as exc:
            raise MaskTokenVaultUnavailable from exc
        if not stored:
            return False
        try:
            record = json.loads(stored)
        except (TypeError, ValueError):
            return False
        if not isinstance(record, dict):
            return False
        return _record_matches(record, binding, current_value)

    def issuance_lease(self, endpoint_id: int):
        from arabase.mcp.protection.capacity import issuance_lease

        return issuance_lease(endpoint_id, self)

    def delete(self, digests: list[str]) -> None:
        if not digests:
            return
        for digest in digests:
            key = f"{MASK_TOKEN_REDIS_PREFIX}{digest}"
            try:
                record = self.redis.get(key)
            except RedisError:
                # An uncertain cleanup keeps the sorted-set reservation until TTL.
                continue
            endpoint_id = None
            try:
                endpoint_id = json.loads(record)["endpoint_id"] if record else None
            except (KeyError, TypeError, ValueError):
                pass
            try:
                deleted = self.redis.delete(key)
                if deleted:
                    self.redis.zrem(MASK_TOKEN_EXPIRY_INDEX, digest)
                    if endpoint_id is not None:
                        self.redis.zrem(
                            f"{MASK_TOKEN_ENDPOINT_INDEX_PREFIX}{endpoint_id}",
                            digest,
                        )
            except RedisError:
                # An uncertain cleanup keeps the sorted-set reservation until TTL.
                pass


def _issued(token: GeneratedMaskToken) -> IssuedMaskToken:
    return IssuedMaskToken(
        raw_handle=token.raw_handle,
        digest=token.digest,
        envelope=token.envelope,
    )


class DatabaseMaskTokenVault:
    """The default vault: mask-token records in the application's PostgreSQL.

    Every deployment already runs PostgreSQL, and every worker and replica shares
    it, so protected fields work without provisioning another service. Records
    are written in the caller's transaction: a response that is never released
    or a mutation that rolls back takes its tokens with it. The same live-record
    limits and issuer admission as the Redis vault apply, enforced with
    transaction-scoped advisory locks that a crashed worker cannot leak.
    """

    def issue(self, binding: MaskTokenBinding, value: Any) -> IssuedMaskToken:
        return self.issue_many([(binding, value)])[0]

    def issue_many(
        self, items: list[tuple[MaskTokenBinding, Any]]
    ) -> list[IssuedMaskToken]:
        from arabase.mcp.protection.models import MCPMaskTokenRecord

        if not items:
            return []
        endpoint_id = items[0][0].endpoint_id
        if any(binding.endpoint_id != endpoint_id for binding, _value in items):
            raise MaskTokenVaultUnavailable
        expires_at, generated = _build_token_records(items)
        try:
            with transaction.atomic():
                # The limits guard against abuse rather than memory here, so
                # reservations are not serialised: that would hold a lock until
                # every protected call commits. The issuer admission (at most six
                # concurrent batches of at most 1,000) bounds any overshoot.
                now = datetime.now(UTC)
                self._purge_expired(now)
                live = MCPMaskTokenRecord.objects.filter(expires_at__gt=now)
                if live.count() + len(generated) > MAX_GLOBAL_TOKENS:
                    raise MaskTokenVaultUnavailable
                if (
                    live.filter(endpoint_id=endpoint_id).count() + len(generated)
                    > MAX_ENDPOINT_TOKENS
                ):
                    raise MaskTokenVaultUnavailable
                MCPMaskTokenRecord.objects.bulk_create(
                    [
                        MCPMaskTokenRecord(
                            digest=token.digest,
                            endpoint_id=endpoint_id,
                            expires_at=expires_at,
                            record=record,
                        )
                        for token, record in generated
                    ]
                )
        except DatabaseError as exc:
            raise MaskTokenVaultUnavailable from exc
        return [_issued(token) for token, _record in generated]

    def redeem(
        self, raw_handle: str, binding: MaskTokenBinding, current_value: Any
    ) -> bool:
        """Validate a same-cell token; non-consuming, like the Redis vault."""

        from arabase.mcp.protection.models import MCPMaskTokenRecord

        try:
            digest = hashlib.sha256(raw_handle.encode("ascii")).hexdigest()
        except (AttributeError, TypeError, UnicodeEncodeError):
            return False
        try:
            stored = (
                MCPMaskTokenRecord.objects.filter(
                    digest=digest, expires_at__gt=datetime.now(UTC)
                )
                .values_list("record", flat=True)
                .first()
            )
        except DatabaseError as exc:
            raise MaskTokenVaultUnavailable from exc
        if not isinstance(stored, dict):
            return False
        return _record_matches(stored, binding, current_value)

    def delete(self, digests: list[str]) -> None:
        from arabase.mcp.protection.models import MCPMaskTokenRecord

        if not digests:
            return
        try:
            with transaction.atomic():
                MCPMaskTokenRecord.objects.filter(digest__in=digests).delete()
        except DatabaseError:
            # The surrounding transaction is failing and takes the records with
            # it; anything that survives still expires.
            pass

    @contextmanager
    def issuance_lease(self, endpoint_id: int) -> Iterator[None]:
        """Admit at most two issuers per endpoint and six deployment-wide.

        The locks are transaction-scoped: they last until the MCP call's
        transaction ends and cannot outlive a worker that dies holding them.
        """

        from arabase.mcp.protection.capacity import (
            ISSUER_WAIT_SECONDS,
            MAX_ACTIVE_ISSUERS_GLOBAL,
            MAX_ACTIVE_ISSUERS_PER_ENDPOINT,
        )

        deadline = time.monotonic() + ISSUER_WAIT_SECONDS
        endpoint_slots = [
            _ISSUER_ENDPOINT_LOCK_BASE + endpoint_id * 4 + slot
            for slot in range(MAX_ACTIVE_ISSUERS_PER_ENDPOINT)
        ]
        global_slots = [
            _ISSUER_GLOBAL_LOCK_BASE + slot for slot in range(MAX_ACTIVE_ISSUERS_GLOBAL)
        ]
        with transaction.atomic():
            try:
                endpoint_acquired = False
                global_acquired = False
                while True:
                    if not endpoint_acquired:
                        endpoint_acquired = _try_any_xact_lock(endpoint_slots)
                    if endpoint_acquired and not global_acquired:
                        global_acquired = _try_any_xact_lock(global_slots)
                    if endpoint_acquired and global_acquired:
                        break
                    if time.monotonic() > deadline:
                        raise MaskTokenVaultUnavailable
                    time.sleep(0.01)
            except DatabaseError as exc:
                raise MaskTokenVaultUnavailable from exc
            yield

    def live_token_count(self) -> int:
        from arabase.mcp.protection.models import MCPMaskTokenRecord

        return MCPMaskTokenRecord.objects.filter(
            expires_at__gt=datetime.now(UTC)
        ).count()

    @staticmethod
    def _purge_expired(now: datetime) -> None:
        from arabase.mcp.protection.models import MCPMaskTokenRecord

        expired = MCPMaskTokenRecord.objects.filter(expires_at__lte=now).values(
            "digest"
        )[:PURGE_BATCH_SIZE]
        MCPMaskTokenRecord.objects.filter(digest__in=expired).delete()


def _try_any_xact_lock(keys: list[int]) -> bool:
    with connection.cursor() as cursor:
        for key in keys:
            cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", [key])
            if cursor.fetchone()[0]:
                return True
    return False


def purge_expired_mask_tokens() -> int:
    """Delete every expired database-vault record; returns how many."""

    from arabase.mcp.protection.models import MCPMaskTokenRecord

    deleted, _ = MCPMaskTokenRecord.objects.filter(
        expires_at__lte=datetime.now(UTC)
    ).delete()
    return deleted


def mask_token_vault_backend() -> str:
    backend = str(settings.MCP_PROTECTION_VAULT or "auto").strip().lower()
    if backend == "auto":
        uses_redis = (
            settings.MCP_PROTECTION_REDIS_URL
            or settings.MCP_PROTECTION_ALLOW_SHARED_REDIS
        )
        return VAULT_BACKEND_REDIS if uses_redis else VAULT_BACKEND_DATABASE
    return backend


def get_mask_token_vault() -> RedisMaskTokenVault | DatabaseMaskTokenVault:
    backend = mask_token_vault_backend()
    if backend == VAULT_BACKEND_DATABASE:
        return DatabaseMaskTokenVault()
    if backend == VAULT_BACKEND_REDIS:
        return RedisMaskTokenVault()
    raise MaskTokenVaultUnavailable
