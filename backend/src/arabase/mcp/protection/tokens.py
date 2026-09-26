import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

MASK_TOKEN_RESERVED_KEY = "$jadawelProtected"
MASK_TOKEN_VERSION = 1
MASK_TOKEN_HANDLE_BYTES = 32


@dataclass(frozen=True, slots=True)
class GeneratedMaskToken:
    raw_handle: str
    digest: str

    @property
    def envelope(self) -> dict:
        return {
            MASK_TOKEN_RESERVED_KEY: {
                "v": MASK_TOKEN_VERSION,
                "token": self.raw_handle,
            }
        }


def generate_mask_token() -> GeneratedMaskToken:
    raw_bytes = secrets.token_bytes(MASK_TOKEN_HANDLE_BYTES)
    raw_handle = base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")
    return GeneratedMaskToken(
        raw_handle=raw_handle,
        digest=mask_token_digest(raw_handle),
    )


def mask_token_digest(handle: str) -> str:
    """Return the vault lookup digest of a raw mask-token handle."""

    return hashlib.sha256(handle.encode("ascii")).hexdigest()


def contains_mask_token_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return MASK_TOKEN_RESERVED_KEY in value or any(
            contains_mask_token_marker(nested) for nested in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(contains_mask_token_marker(nested) for nested in value)
    return False


def extract_mask_token_handle(value: Any) -> str | None:
    """Return a syntactically valid raw handle from an exact token envelope.

    The envelope is deliberately strict.  A token-looking object nested inside a
    user value is not a protected-cell redemption and must never be forwarded to
    the row service as ordinary data.
    """

    if not isinstance(value, dict) or set(value) != {MASK_TOKEN_RESERVED_KEY}:
        return None
    payload = value.get(MASK_TOKEN_RESERVED_KEY)
    if not isinstance(payload, dict) or set(payload) != {"v", "token"}:
        return None
    if payload.get("v") != MASK_TOKEN_VERSION:
        return None
    handle = payload.get("token")
    if not isinstance(handle, str) or not handle or "=" in handle:
        return None
    try:
        decoded = base64.urlsafe_b64decode(handle + "=" * (-len(handle) % 4))
    except (ValueError, UnicodeEncodeError):
        return None
    if len(decoded) != MASK_TOKEN_HANDLE_BYTES:
        return None
    try:
        canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    except UnicodeDecodeError:
        return None
    return handle if canonical == handle else None
