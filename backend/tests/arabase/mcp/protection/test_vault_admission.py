import base64

from django.shortcuts import reverse
from django.test import override_settings

import fakeredis
import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

import arabase.mcp.protection.readiness as readiness
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.readiness import MCPProtectionReadiness
from arabase.mcp.protection.vault import RedisMaskTokenVault
from jadawel.core.mcp.models import MCPEndpoint

FINGERPRINT_KEY = base64.b64encode(b"f" * 32).decode()


@pytest.fixture
def vault_not_ready(monkeypatch):
    # The database vault is ready in tests; simulate a vault that is not.
    monkeypatch.setattr(
        "arabase.mcp.protection.admission.check_mask_token_vault_readiness",
        lambda: MCPProtectionReadiness(
            False, MCPProtectionSafeReason.PROTECTION_REDIS_UNAVAILABLE
        ),
    )


def _bounded_fake_redis(monkeypatch):
    redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(
        redis,
        "config_get",
        lambda name: (
            {"maxmemory": str(128 * 1024 * 1024)}
            if name == "maxmemory"
            else {"maxmemory-policy": "noeviction"}
        ),
    )
    # fakeredis does not implement INFO.
    monkeypatch.setattr(redis, "info", lambda section: {"used_memory": 1024})
    vault = RedisMaskTokenVault(redis_client=redis)
    monkeypatch.setattr(readiness, "get_mask_token_vault", lambda: vault)


@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_vault_readiness_passes_with_bounded_redis_and_active_key(monkeypatch):
    _bounded_fake_redis(monkeypatch)

    result = readiness.check_mask_token_vault_readiness()

    assert result == MCPProtectionReadiness(True, MCPProtectionSafeReason.NONE)


@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_vault_readiness_fails_when_the_fingerprint_key_is_missing(monkeypatch):
    # Redis alone passing used to report ready, yet every protected read then
    # failed when token issuance could not load the key.
    _bounded_fake_redis(monkeypatch)

    result = readiness.check_mask_token_vault_readiness()

    assert result.ready is False
    assert result.safe_reason_code == "PROTECTION_KEY_UNAVAILABLE"


@override_settings(
    MCP_PROTECTION_VAULT="redis",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)
def test_vault_readiness_fails_when_redis_is_selected_but_not_configured():
    result = readiness.check_mask_token_vault_readiness()

    assert result.ready is False
    assert result.safe_reason_code == "PROTECTION_REDIS_UNAVAILABLE"


@pytest.mark.django_db
def test_protected_endpoint_is_refused_while_the_vault_is_not_ready(
    api_client, data_fixture, vault_not_ready
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table, name="National ID")

    response = api_client.post(
        reverse("api:arabase:mcp_endpoint_protection_summaries"),
        {
            "name": "Protected assistant",
            "workspace_id": workspace.id,
            "protected_field_ids": [field.id],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="vault-not-ready-0001",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_MCP_PROTECTION_NOT_READY"
    assert "PROTECTION_REDIS_UNAVAILABLE" in response.json()["detail"]
    assert MCPEndpoint.objects.count() == 0


@pytest.mark.django_db
def test_unprotected_endpoint_is_still_created_while_the_vault_is_not_ready(
    api_client, data_fixture, vault_not_ready
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)

    response = api_client.post(
        reverse("api:arabase:mcp_endpoint_protection_summaries"),
        {
            "name": "Plain assistant",
            "workspace_id": workspace.id,
            "protected_field_ids": [],
            "confirm_empty_policy": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="vault-not-ready-0002",
    )

    assert response.status_code == 201
    assert MCPEndpoint.objects.count() == 1


def _policy_url(endpoint):
    return reverse(
        "api:arabase:mcp_protection_policy", kwargs={"endpoint_id": endpoint.id}
    )


@pytest.mark.django_db
def test_adding_a_protected_field_is_refused_while_the_vault_is_not_ready(
    api_client, data_fixture, vault_not_ready
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)

    response = api_client.patch(
        _policy_url(endpoint),
        {"protected_field_ids": [field.id], "expected_revision": 1},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="vault-not-ready-0003",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_MCP_PROTECTION_NOT_READY"
    assert not MCPProtectedField.objects.filter(
        policy=endpoint.arabase_protection_policy
    ).exists()


@pytest.mark.django_db
def test_removing_protection_is_allowed_while_the_vault_is_not_ready(
    api_client, data_fixture, vault_not_ready
):
    # The recovery path during an outage: an owner can always drop protection.
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )

    response = api_client.patch(
        _policy_url(endpoint),
        {
            "protected_field_ids": [],
            "expected_revision": 1,
            "confirm_remove_field_ids": [field.id],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="vault-not-ready-0004",
    )

    assert response.status_code == HTTP_200_OK
    assert not MCPProtectedField.objects.filter(
        policy=endpoint.arabase_protection_policy
    ).exists()
