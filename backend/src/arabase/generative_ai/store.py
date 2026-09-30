"""Where admin-managed AI provider settings are kept and read.

``get_instance_setting`` is what core's ``GenerativeAIModelType`` calls once a
workspace has no value of its own (see PATCHES.md). It is on the path of every
AI call and of every workspace payload, so the rows are cached, still sealed,
and the cache is dropped whenever an admin saves.
"""

from typing import Any, Optional

from django.core.cache import cache

from arabase.sealing import Sealer

# The providers administrators can configure, in display order. The labels are
# the providers' own product names.
MANAGED_PROVIDERS = ("openai", "anthropic", "ollama", "openrouter")

DISABLED_PROVIDERS = ("mistral",)
"""Registered by core but switched off in this fork for now. The provider code
is untouched: removing a name here is all it takes to offer it again."""

PROVIDER_FIELDS = {
    "openai": ("api_key", "models", "organization", "base_url"),
    "anthropic": ("api_key", "models"),
    "ollama": ("host", "models"),
    "openrouter": ("api_key", "models", "organization"),
}

CACHE_KEY = "arabase:generative_ai:provider_settings"
CACHE_SECONDS = 300

_SEALER = Sealer("arabase.generative_ai", "provider-api-key")


def seal(value: str) -> str:
    return _SEALER.seal(value)


def unseal(value: str) -> Optional[str]:
    """The plain key, or None when it was sealed under another SECRET_KEY."""

    return _SEALER.unseal(value)


def _load() -> dict[str, dict[str, Any]]:
    rows = cache.get(CACHE_KEY)
    if rows is None:
        from arabase.generative_ai.models import GenerativeAIProviderSettings

        rows = {
            row.provider: {
                "api_key_sealed": row.api_key_sealed,
                "models": list(row.enabled_models or []),
                "host": row.host,
                "base_url": row.base_url,
                "organization": row.organization,
            }
            for row in GenerativeAIProviderSettings.objects.all()
        }
        cache.set(CACHE_KEY, rows, CACHE_SECONDS)
    return rows


def invalidate() -> None:
    cache.delete(CACHE_KEY)


def get_instance_setting(provider: str, key: str) -> Any:
    """An admin-set value for ``provider``, or None to fall through to env."""

    if provider not in MANAGED_PROVIDERS or key not in PROVIDER_FIELDS[provider]:
        return None
    row = _load().get(provider)
    if not row:
        return None
    if key == "api_key":
        return unseal(row["api_key_sealed"]) if row["api_key_sealed"] else None
    return row.get(key) or None
