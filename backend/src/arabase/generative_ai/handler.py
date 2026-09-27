"""Reading and changing the admin-managed AI provider settings."""

from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import transaction

from arabase.generative_ai import store
from arabase.generative_ai.models import GenerativeAIProviderSettings

ENVIRONMENT_SETTING = {
    "openai": "JADAWEL_OPENAI_API_KEY",
    "anthropic": "JADAWEL_ANTHROPIC_API_KEY",
    "ollama": "JADAWEL_OLLAMA_HOST",
    "openrouter": "JADAWEL_OPENROUTER_API_KEY",
}


class ProviderNotManaged(Exception):
    """Not one of the providers administrators can configure."""


class InvalidProviderSettings(ValueError):
    """A value the provider cannot use; the message says which one."""


def apply_provider_policy() -> None:
    """Switch off the disabled providers and plug in the admin settings.

    A disabled provider stays registered under its own type, so anything that
    already refers to it still resolves; it simply reports no models and is
    never enabled, whatever the environment says.
    """

    from jadawel.core.generative_ai.registries import (
        generative_ai_model_type_registry as registry,
    )

    for name in store.DISABLED_PROVIDERS:
        if name not in registry.registry:
            continue
        original = registry.get(name).__class__

        class DisabledProvider(original):
            def is_enabled(self, workspace=None, settings_override=None):
                return False

            def get_enabled_models(self, workspace=None, settings_override=None):
                return []

        DisabledProvider.__name__ = f"Disabled{original.__name__}"
        registry.unregister(name)
        registry.register(DisabledProvider())

    registry.instance_settings_getter = store.get_instance_setting


def list_provider_settings() -> list[dict]:
    from jadawel.core.generative_ai.registries import (
        generative_ai_model_type_registry as registry,
    )

    rows = {row.provider: row for row in GenerativeAIProviderSettings.objects.all()}
    providers = []
    for provider in store.MANAGED_PROVIDERS:
        row = rows.get(provider)
        providers.append(
            {
                "type": provider,
                "fields": list(store.PROVIDER_FIELDS[provider]),
                "api_key_set": bool(row and row.api_key_sealed),
                "api_key_hint": row.api_key_hint if row else "",
                "models": list(row.enabled_models) if row else [],
                "host": row.host if row else "",
                "base_url": row.base_url if row else "",
                "organization": row.organization if row else "",
                "configured_by_environment": bool(
                    getattr(settings, ENVIRONMENT_SETTING[provider], None)
                ),
                "enabled": registry.get(provider).is_enabled(),
                "updated_on": row.updated_on if row else None,
            }
        )
    return providers


def _clean_url(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidProviderSettings(f"{name} must be an http(s) URL.")
    return value.rstrip("/")


def _clean_models(models: list[str]) -> list[str]:
    cleaned = []
    for model in models:
        model = model.strip()
        if model and model not in cleaned:
            cleaned.append(model)
    return cleaned


def update_provider_settings(
    user: AbstractUser,
    provider: str,
    *,
    api_key: Optional[str] = None,
    clear_api_key: bool = False,
    models: Optional[list[str]] = None,
    host: Optional[str] = None,
    base_url: Optional[str] = None,
    organization: Optional[str] = None,
) -> None:
    """Change only the values given; a blank ``api_key`` keeps the saved one.

    :raises ProviderNotManaged: for a provider admins cannot configure,
        including the disabled ones.
    :raises InvalidProviderSettings: for a value the provider cannot use.
    """

    if provider not in store.MANAGED_PROVIDERS:
        raise ProviderNotManaged(provider)
    allowed = store.PROVIDER_FIELDS[provider]
    given = {
        "api_key": api_key or clear_api_key or None,
        "models": models,
        "host": host,
        "base_url": base_url,
        "organization": organization,
    }
    unexpected = [key for key, value in given.items() if value and key not in allowed]
    if unexpected:
        raise InvalidProviderSettings(
            f"{provider} does not take: {', '.join(unexpected)}."
        )

    with transaction.atomic():
        row, _ = GenerativeAIProviderSettings.objects.select_for_update().get_or_create(
            provider=provider
        )
        if clear_api_key:
            row.api_key_sealed, row.api_key_hint = "", ""
        elif api_key and api_key.strip():
            key = api_key.strip()
            row.api_key_sealed = store.seal(key)
            row.api_key_hint = key[-4:] if len(key) > 8 else ""
        if models is not None:
            row.enabled_models = _clean_models(models)
        if host is not None:
            row.host = _clean_url(host, "host")
        if base_url is not None:
            row.base_url = _clean_url(base_url, "base_url")
        if organization is not None:
            row.organization = organization.strip()
        row.updated_by = user
        row.save()
        transaction.on_commit(store.invalidate)
    store.invalidate()


def delete_provider_settings(provider: str) -> None:
    if provider not in store.MANAGED_PROVIDERS:
        raise ProviderNotManaged(provider)
    GenerativeAIProviderSettings.objects.filter(provider=provider).delete()
    transaction.on_commit(store.invalidate)
    store.invalidate()
