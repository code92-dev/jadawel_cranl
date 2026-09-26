"""The default mask-token vault, kept in the application's PostgreSQL.

The only vault module that imports a model.
"""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from django.db import DatabaseError, connection, transaction
from django.db.models import Count, Q

from arabase.mcp.protection import limits
from arabase.mcp.protection.models import MCPMaskTokenRecord
from arabase.mcp.protection.tokens import mask_token_digest
from arabase.mcp.protection.vault.records import (
    VAULT_BACKEND_DATABASE,
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    build_token_records,
    record_matches,
    single_endpoint_id,
)

if TYPE_CHECKING:
    from arabase.mcp.protection.tokens import GeneratedMaskToken

# PostgreSQL advisory-lock keys for database-vault issuer admission, in a
# namespace no other Jadawel code uses (0x4A4D5043, "JMPC").
_ISSUER_GLOBAL_LOCK_BASE = 0x4A4D5043 << 32
_ISSUER_ENDPOINT_LOCK_BASE = 0x4A4D5044 << 32


class DatabaseMaskTokenVault:
    """The default vault: mask-token records in the application's PostgreSQL.

    Every deployment already runs PostgreSQL, and every worker and replica shares
    it, so protected fields work without provisioning another service. Records
    are written in the caller's transaction: a response that is never released
    or a mutation that rolls back takes its tokens with it. The same live-record
    limits and issuer admission as the Redis vault apply, enforced with
    transaction-scoped advisory locks that a crashed worker cannot leak.
    """

    backend: ClassVar[str] = VAULT_BACKEND_DATABASE

    def issue_many(
        self, items: list[tuple[MaskTokenBinding, Any]]
    ) -> list["GeneratedMaskToken"]:
        if not items:
            return []
        endpoint_id = single_endpoint_id(items)
        expires_at, generated = build_token_records(items)
        try:
            with transaction.atomic():
                # The limits guard against abuse rather than memory here, so
                # reservations are not serialised: that would hold a lock until
                # every protected call commits. The issuer admission (at most six
                # concurrent batches of at most 1,000) bounds any overshoot.
                now = datetime.now(UTC)
                purge_expired_mask_tokens(now=now, limit=limits.PURGE_BATCH_SIZE)
                live = MCPMaskTokenRecord.objects.filter(expires_at__gt=now).aggregate(
                    total=Count("pk"),
                    endpoint=Count("pk", filter=Q(endpoint_id=endpoint_id)),
                )
                if live["total"] + len(generated) > limits.MAX_GLOBAL_TOKENS:
                    raise MaskTokenVaultUnavailable
                if live["endpoint"] + len(generated) > limits.MAX_ENDPOINT_TOKENS:
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
        return [token for token, _record in generated]

    def redeem(
        self, raw_handle: str, binding: MaskTokenBinding, current_value: Any
    ) -> bool:
        """Validate a same-cell token; non-consuming, like the Redis vault."""

        try:
            digest = mask_token_digest(raw_handle)
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
        return record_matches(stored, binding, current_value)

    def delete(self, digests: list[str]) -> None:
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

        deadline = time.monotonic() + limits.ISSUER_WAIT_SECONDS
        endpoint_slots = [
            _ISSUER_ENDPOINT_LOCK_BASE + endpoint_id * 4 + slot
            for slot in range(limits.MAX_ACTIVE_ISSUERS_PER_ENDPOINT)
        ]
        global_slots = [
            _ISSUER_GLOBAL_LOCK_BASE + slot
            for slot in range(limits.MAX_ACTIVE_ISSUERS_GLOBAL)
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

    def is_ready(self) -> bool:
        """The table is reachable and has room for one more full batch."""

        try:
            started = time.monotonic()
            live_tokens = MCPMaskTokenRecord.objects.filter(
                expires_at__gt=datetime.now(UTC)
            ).count()
            if (
                live_tokens + limits.MAX_ISSUED_OR_REDEEMED_PER_CALL
                >= limits.MAX_GLOBAL_TOKENS
            ):
                raise MaskTokenVaultUnavailable
            if time.monotonic() - started > limits.READINESS_OPERATION_TIMEOUT_SECONDS:
                raise MaskTokenVaultUnavailable
        except (MaskTokenVaultUnavailable, DatabaseError):
            return False
        return True


def _try_any_xact_lock(keys: list[int]) -> bool:
    with connection.cursor() as cursor:
        for key in keys:
            cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", [key])
            if cursor.fetchone()[0]:
                return True
    return False


def purge_expired_mask_tokens(
    *, now: datetime | None = None, limit: int | None = None
) -> int:
    """Delete expired database-vault records; returns how many.

    Without ``limit`` every expired record goes; with it, at most ``limit``.
    """

    expired = MCPMaskTokenRecord.objects.filter(
        expires_at__lte=now or datetime.now(UTC)
    )
    if limit is not None:
        expired = MCPMaskTokenRecord.objects.filter(
            digest__in=expired.values("digest")[:limit]
        )
    deleted, _ = expired.delete()
    return deleted
