"""Admin-managed AI provider keys (docs/SANAD_AI_ASSISTANT.md, "Configuration").

Administrators set provider keys in the admin settings page. Keys are sealed at
rest and never returned; every AI feature then reads them through core's
provider registry, ahead of the environment variables. Mistral is disabled.
"""

import json

from django.shortcuts import reverse
from django.test import override_settings

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from arabase.generative_ai import store
from arabase.generative_ai.models import GenerativeAIProviderSettings
from jadawel.core.generative_ai.registries import generative_ai_model_type_registry

LIST_URL = "api:arabase:admin_generative_ai"
KEY = "sk-live-abcdefghijklmnop1234"

# Isolate every test from whatever the machine's environment configures.
NO_ENV = {
    "JADAWEL_OPENAI_API_KEY": None,
    "JADAWEL_OPENAI_MODELS": [],
    "JADAWEL_ANTHROPIC_API_KEY": None,
    "JADAWEL_ANTHROPIC_MODELS": [],
    "JADAWEL_OLLAMA_HOST": None,
    "JADAWEL_OLLAMA_MODELS": [],
    "JADAWEL_OPENROUTER_API_KEY": None,
    "JADAWEL_OPENROUTER_MODELS": [],
    "JADAWEL_MISTRAL_API_KEY": None,
    "JADAWEL_MISTRAL_MODELS": [],
}


def provider_url(provider):
    return reverse(
        "api:arabase:admin_generative_ai_provider", kwargs={"provider": provider}
    )


@pytest.fixture
def admin(data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    return {"user": user, "headers": {"HTTP_AUTHORIZATION": f"JWT {token}"}}


def patch(api_client, admin, provider, **body):
    return api_client.patch(
        provider_url(provider), body, format="json", **admin["headers"]
    )


def by_type(response):
    return {item["type"]: item for item in response.json()["providers"]}


@pytest.mark.django_db
def test_only_administrators_reach_the_settings(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=False)
    member = {"HTTP_AUTHORIZATION": f"JWT {token}"}

    assert api_client.get(reverse(LIST_URL)).status_code == HTTP_401_UNAUTHORIZED
    assert api_client.get(reverse(LIST_URL), **member).status_code == (
        HTTP_403_FORBIDDEN
    )
    response = api_client.patch(
        provider_url("openai"), {"api_key": KEY}, format="json", **member
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    assert not GenerativeAIProviderSettings.objects.exists()


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_only_the_four_providers_are_offered(api_client, admin):
    response = api_client.get(reverse(LIST_URL), **admin["headers"])

    assert response.status_code == HTTP_200_OK
    assert [p["type"] for p in response.json()["providers"]] == [
        "openai",
        "anthropic",
        "ollama",
        "openrouter",
    ]
    assert by_type(response)["ollama"]["fields"] == ["host", "models"]


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_a_saved_key_is_sealed_and_never_returned(api_client, admin, data_fixture):
    workspace = data_fixture.create_workspace(user=admin["user"])

    response = patch(
        api_client, admin, "openai", api_key=KEY, models=["gpt-5", " gpt-5-mini ", ""]
    )

    assert response.status_code == HTTP_200_OK
    assert KEY not in json.dumps(response.json())
    openai = by_type(response)["openai"]
    assert openai["api_key_set"] is True
    assert openai["api_key_hint"] == "1234"
    assert openai["models"] == ["gpt-5", "gpt-5-mini"]
    assert openai["enabled"] is True
    row = GenerativeAIProviderSettings.objects.get(provider="openai")
    assert KEY not in row.api_key_sealed
    assert row.updated_by == admin["user"]

    # Every AI feature reads it through core's registry.
    provider = generative_ai_model_type_registry.get("openai")
    assert provider.get_api_key() == KEY
    assert generative_ai_model_type_registry.get_enabled_models_per_type(workspace) == {
        "openai": ["gpt-5", "gpt-5-mini"]
    }


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_sanad_offers_the_models_admins_enable(api_client, admin, data_fixture):
    workspace = data_fixture.create_workspace(user=admin["user"])
    url = reverse("api:arabase:sanad_models", kwargs={"workspace_id": workspace.id})

    assert api_client.get(url, **admin["headers"]).json() == {"models": []}
    patch(api_client, admin, "anthropic", api_key=KEY, models=["claude-sonnet-5"])

    assert api_client.get(url, **admin["headers"]).json() == {
        "models": ["anthropic/claude-sonnet-5"]
    }


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_a_blank_key_keeps_the_saved_one_and_clearing_removes_it(api_client, admin):
    patch(api_client, admin, "openrouter", api_key=KEY, models=["x/y"])
    provider = generative_ai_model_type_registry.get("openrouter")

    patch(api_client, admin, "openrouter", api_key="", models=["x/z"])
    assert provider.get_api_key() == KEY
    assert provider.get_enabled_models() == ["x/z"]

    response = patch(api_client, admin, "openrouter", clear_api_key=True)
    assert by_type(response)["openrouter"]["api_key_set"] is False
    assert provider.get_api_key() is None
    assert provider.is_enabled() is False


@pytest.mark.django_db
@override_settings(
    **{**NO_ENV, "JADAWEL_OPENAI_API_KEY": "env-key", "JADAWEL_OPENAI_MODELS": ["env"]}
)
def test_admin_settings_come_before_the_environment(api_client, admin):
    provider = generative_ai_model_type_registry.get("openai")
    assert provider.get_api_key() == "env-key"

    response = patch(api_client, admin, "openai", api_key=KEY, models=["gpt-5"])
    assert by_type(response)["openai"]["configured_by_environment"] is True
    assert provider.get_api_key() == KEY
    assert provider.get_enabled_models() == ["gpt-5"]

    # Removing the admin settings falls back to the environment again.
    api_client.delete(provider_url("openai"), **admin["headers"])
    assert provider.get_api_key() == "env-key"
    assert provider.get_enabled_models() == ["env"]


@pytest.mark.django_db
@override_settings(
    **{
        **NO_ENV,
        "JADAWEL_MISTRAL_API_KEY": "mistral-key",
        "JADAWEL_MISTRAL_MODELS": ["mistral-large"],
    }
)
def test_mistral_is_disabled_even_when_the_environment_configures_it(
    api_client, admin, data_fixture
):
    workspace = data_fixture.create_workspace(user=admin["user"])
    mistral = generative_ai_model_type_registry.get("mistral")

    # Still registered, so anything that refers to it resolves...
    assert mistral.type == "mistral"
    # ...but never enabled and never offered.
    assert mistral.is_enabled() is False
    assert mistral.get_enabled_models() == []
    assert "mistral" not in (
        generative_ai_model_type_registry.get_enabled_models_per_type(workspace)
    )
    response = patch(api_client, admin, "mistral", api_key=KEY, models=["m"])
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_AI_PROVIDER_NOT_MANAGED"


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_invalid_values_are_rejected(api_client, admin):
    response = patch(api_client, admin, "ollama", host="localhost:11434")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_AI_PROVIDER_SETTINGS_INVALID"
    assert "http" in response.json()["detail"]

    response = patch(api_client, admin, "anthropic", host="http://ollama:11434")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "host" in response.json()["detail"]

    response = patch(
        api_client, admin, "ollama", host="http://ollama:11434/", models=["llama3"]
    )
    assert response.status_code == HTTP_200_OK
    ollama = generative_ai_model_type_registry.get("ollama")
    assert ollama.get_host() == "http://ollama:11434"
    assert ollama.is_enabled() is True


@pytest.mark.django_db
@override_settings(**NO_ENV)
def test_a_key_sealed_under_another_secret_key_is_ignored(api_client, admin):
    patch(api_client, admin, "openai", api_key=KEY, models=["gpt-5"])
    store.invalidate()

    with override_settings(SECRET_KEY="a-different-secret-key-for-this-test"):
        provider = generative_ai_model_type_registry.get("openai")
        assert provider.get_api_key() is None
        assert provider.is_enabled() is False
