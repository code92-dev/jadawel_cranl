from django.conf import settings

from arabase.mcp.protection.vault.database_backend import (
    DatabaseMaskTokenVault,
    purge_expired_mask_tokens,
)
from arabase.mcp.protection.vault.records import (
    VAULT_BACKEND_DATABASE,
    VAULT_BACKEND_REDIS,
    MaskTokenBinding,
    MaskTokenVault,
    MaskTokenVaultUnavailable,
    load_active_fingerprint_key,
)
from arabase.mcp.protection.vault.redis_backend import (
    MASK_TOKEN_EXPIRY_INDEX,
    MASK_TOKEN_REDIS_PREFIX,
    RedisMaskTokenVault,
)

__all__ = [
    "MASK_TOKEN_EXPIRY_INDEX",
    "MASK_TOKEN_REDIS_PREFIX",
    "VAULT_BACKEND_DATABASE",
    "VAULT_BACKEND_REDIS",
    "DatabaseMaskTokenVault",
    "MaskTokenBinding",
    "MaskTokenVault",
    "MaskTokenVaultUnavailable",
    "RedisMaskTokenVault",
    "get_mask_token_vault",
    "load_active_fingerprint_key",
    "mask_token_vault_backend",
    "purge_expired_mask_tokens",
]


def mask_token_vault_backend() -> str:
    backend = str(settings.MCP_PROTECTION_VAULT or "auto").strip().lower()
    if backend == "auto":
        uses_redis = (
            settings.MCP_PROTECTION_REDIS_URL
            or settings.MCP_PROTECTION_ALLOW_SHARED_REDIS
        )
        return VAULT_BACKEND_REDIS if uses_redis else VAULT_BACKEND_DATABASE
    return backend


def get_mask_token_vault() -> MaskTokenVault:
    backend = mask_token_vault_backend()
    if backend == VAULT_BACKEND_DATABASE:
        return DatabaseMaskTokenVault()
    if backend == VAULT_BACKEND_REDIS:
        return RedisMaskTokenVault()
    raise MaskTokenVaultUnavailable
