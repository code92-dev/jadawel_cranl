"""Backend-neutral mask-token records: bindings, fingerprints and the Protocol.

Imports no model, database or Redis module, so both vault backends share it.
"""

import base64
import hashlib
import hmac
import json
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar, Protocol

from django.conf import settings
from django.utils.crypto import salted_hmac

from arabase.mcp.protection import limits
from arabase.mcp.protection.tokens import GeneratedMaskToken, generate_mask_token

DERIVED_FINGERPRINT_KEY_ID = "secret-derived-v1"
DERIVED_FINGERPRINT_KEY_SALT = "jadawel.mcp-protection.fingerprint-key.v1"
VAULT_BACKEND_DATABASE = "database"
VAULT_BACKEND_REDIS = "redis"


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


class MaskTokenVault(Protocol):
    """What every mask-token vault backend provides."""

    backend: ClassVar[str]

    def issue_many(
        self, items: list[tuple[MaskTokenBinding, Any]]
    ) -> list[GeneratedMaskToken]: ...

    def redeem(
        self, raw_handle: str, binding: MaskTokenBinding, current_value: Any
    ) -> bool: ...

    def delete(self, digests: list[str]) -> None: ...

    def issuance_lease(self, endpoint_id: int) -> AbstractContextManager[None]: ...

    def is_ready(self) -> bool: ...


CANONICAL_VALUE_VERSION = 1


def canonicalize_typed_value(field_type: str, value: Any) -> bytes:
    """Return the stable bytes fingerprinted for one serialized field value."""

    return json.dumps(
        {
            "field_type": field_type,
            "v": CANONICAL_VALUE_VERSION,
            "value": value,
        },
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


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


def load_active_fingerprint_key() -> tuple[str, bytes]:
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


def _fingerprint(fingerprint_key: bytes, field_type: str, value: Any) -> str:
    """The keyed fingerprint of one canonicalized field value."""

    canonical_value = canonicalize_typed_value(field_type, value)
    return hmac.new(fingerprint_key, canonical_value, hashlib.sha256).hexdigest()


def single_endpoint_id(items: list[tuple[MaskTokenBinding, Any]]) -> int:
    """The one endpoint a non-empty issuance batch belongs to."""

    endpoint_id = items[0][0].endpoint_id
    if any(binding.endpoint_id != endpoint_id for binding, _value in items):
        raise MaskTokenVaultUnavailable
    return endpoint_id


def build_token_records(
    items: list[tuple[MaskTokenBinding, Any]],
) -> tuple[datetime, list[tuple[GeneratedMaskToken, dict]]]:
    """Generate one fresh token and its binding record per protected value."""

    key_id, fingerprint_key = load_active_fingerprint_key()
    expires_at = datetime.now(UTC) + timedelta(seconds=limits.MASK_TOKEN_TTL_SECONDS)
    generated: list[tuple[GeneratedMaskToken, dict]] = []
    for binding, value in items:
        fingerprint = _fingerprint(fingerprint_key, binding.field_type, value)
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


def record_matches(record: dict, binding: MaskTokenBinding, current_value) -> bool:
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
        fingerprint = _fingerprint(fingerprint_key, binding.field_type, current_value)
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
