"""The dedicated-Redis mask-token vault and its distributed issuer admission.

Imports no Django model or database module.
"""

import json
import logging
import os
import secrets
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings

from redis import Redis
from redis.exceptions import RedisError

from arabase.mcp.protection import limits
from arabase.mcp.protection.tokens import mask_token_digest
from arabase.mcp.protection.vault.records import (
    VAULT_BACKEND_REDIS,
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    build_token_records,
    record_matches,
    single_endpoint_id,
)

if TYPE_CHECKING:
    from arabase.mcp.protection.tokens import GeneratedMaskToken

# Readiness alerts keep the logger name they were raised under before the move.
logger = logging.getLogger("arabase.mcp.protection.readiness")

MASK_TOKEN_REDIS_PREFIX = "jadawel:mcp-protection:v1:"
MASK_TOKEN_EXPIRY_INDEX = f"{MASK_TOKEN_REDIS_PREFIX}expiry"
MASK_TOKEN_ENDPOINT_INDEX_PREFIX = f"{MASK_TOKEN_REDIS_PREFIX}endpoint:"
ISSUER_INDEX = f"{MASK_TOKEN_REDIS_PREFIX}issuers"
ISSUER_ENDPOINT_INDEX_PREFIX = f"{MASK_TOKEN_REDIS_PREFIX}issuers:endpoint:"

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

_ACQUIRE_SCRIPT = """
local now = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[3]) then
  return 0
end
if redis.call('ZCARD', KEYS[2]) >= tonumber(ARGV[2]) then
  return 0
end
redis.call('ZADD', KEYS[1], ARGV[1], ARGV[4])
redis.call('ZADD', KEYS[2], ARGV[1], ARGV[4])
return 1
"""


# One client, and so one connection pool, per URL and process. A vault is
# built for every protected call; the pid in the key keeps a forked worker from
# reusing its parent's sockets.
_CLIENTS: dict[tuple[str, int], Redis] = {}


def _client_for_url(url: str) -> Redis:
    """Return this process's shared client for ``url``, creating it once.

    A URL that ``Redis.from_url`` rejects raises ``MaskTokenVaultUnavailable``
    and is not cached.
    """

    key = (url, os.getpid())
    client = _CLIENTS.get(key)
    if client is None:
        try:
            client = Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.5,
            )
        except (TypeError, ValueError) as exc:
            raise MaskTokenVaultUnavailable from exc
        _CLIENTS[key] = client
    return client


def redis_memory_ratio(redis) -> float:
    """Return used/max memory of a bounded ``noeviction`` Redis.

    Raises ``RedisError`` when the configuration cannot be verified or the
    server is not a bounded ``noeviction`` vault; catches nothing itself.
    """

    config_get = getattr(redis, "config_get", None)
    if config_get is None:
        raise RedisError("Redis configuration cannot be verified")
    memory = config_get("maxmemory")
    policy = config_get("maxmemory-policy")
    maxmemory = int(memory.get("maxmemory", 0))
    if maxmemory <= 0 or policy.get("maxmemory-policy") != "noeviction":
        raise RedisError("Redis is not a bounded noeviction vault")
    used_memory = int(redis.info("memory").get("used_memory", 0))
    return used_memory / maxmemory


class RedisMaskTokenVault:
    """Digest-addressed Redis vault which never persists the token or value."""

    backend: ClassVar[str] = VAULT_BACKEND_REDIS

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
        self.redis = _client_for_url(redis_url)

    def issue_many(
        self, items: list[tuple[MaskTokenBinding, Any]]
    ) -> list["GeneratedMaskToken"]:
        """Issue one endpoint's tokens with one atomic Redis script."""

        if not items:
            return []
        endpoint_id = single_endpoint_id(items)
        self._ensure_issuance_headroom()
        expires_at, built = build_token_records(items)
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
                    limits.MASK_TOKEN_TTL_SECONDS,
                    limits.MAX_GLOBAL_TOKENS,
                    limits.MAX_ENDPOINT_TOKENS,
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
        return [token for token, _record in generated]

    def _ensure_issuance_headroom(self) -> None:
        """Stop new issuance before the dedicated vault reaches its safety floor.

        Test fakes and explicitly injected Redis clients are deliberately exempt:
        production clients are always constructed from the configured URL and
        therefore get the bounded configuration check on every issuance batch.
        """

        if not self._enforce_memory_headroom:
            return
        try:
            if redis_memory_ratio(self.redis) >= limits.MAX_ISSUANCE_MEMORY_RATIO:
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
            digest = mask_token_digest(raw_handle)
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
        return record_matches(record, binding, current_value)

    def issuance_lease(self, endpoint_id: int):
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

    def is_ready(self) -> bool:
        """Prove the vault is bounded, ``noeviction``, writable and has headroom."""

        try:
            redis = self.redis
            started = time.monotonic()
            redis.ping()
            memory_ratio = redis_memory_ratio(redis)
            if memory_ratio >= limits.REDIS_MEMORY_ALERT_RATIO:
                logger.error(
                    "MCP protection Redis memory alert: %.3f used", memory_ratio
                )
            if memory_ratio >= limits.MAX_ISSUANCE_MEMORY_RATIO:
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
            if (
                live_tokens + limits.MAX_ISSUED_OR_REDEEMED_PER_CALL
                >= limits.MAX_GLOBAL_TOKENS
            ):
                raise RedisError("Redis token reservation headroom is exhausted")
            if time.monotonic() - started > limits.READINESS_OPERATION_TIMEOUT_SECONDS:
                raise RedisError("Redis readiness exceeded its bounded timeout")
        except (MaskTokenVaultUnavailable, RedisError, OSError, ValueError, TypeError):
            return False
        return True


@contextmanager
def issuance_lease(
    endpoint_id: int,
    vault: RedisMaskTokenVault,
) -> Iterator[None]:
    """Admit at most two endpoint and six deployment-wide issuers."""

    member = uuid.uuid4().hex
    endpoint_key = f"{ISSUER_ENDPOINT_INDEX_PREFIX}{endpoint_id}"
    deadline = time.monotonic() + limits.ISSUER_WAIT_SECONDS
    acquired = False
    try:
        while time.monotonic() <= deadline:
            try:
                expires_at = int(time.time()) + limits.ISSUER_LEASE_SECONDS
                acquired = (
                    vault.redis.register_script(_ACQUIRE_SCRIPT)(
                        keys=[ISSUER_INDEX, endpoint_key],
                        args=[
                            expires_at,
                            limits.MAX_ACTIVE_ISSUERS_PER_ENDPOINT,
                            limits.MAX_ACTIVE_ISSUERS_GLOBAL,
                            member,
                        ],
                    )
                    == 1
                )
            except RedisError as exc:
                raise MaskTokenVaultUnavailable from exc
            if acquired:
                break
            time.sleep(0.01)
        if not acquired:
            raise MaskTokenVaultUnavailable
        yield
    finally:
        if acquired:
            try:
                vault.redis.zrem(ISSUER_INDEX, member)
                vault.redis.zrem(endpoint_key, member)
            except RedisError:
                # The short lease expires on its own. Never turn a successful
                # protected response into a plaintext fallback because cleanup
                # was uncertain.
                pass
