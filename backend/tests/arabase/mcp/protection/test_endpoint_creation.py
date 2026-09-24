from django.shortcuts import reverse
from django.test import override_settings

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from arabase.mcp.protection.creation import create_protected_mcp_endpoint
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectionCommand,
    MCPProtectionLifecycleAudit,
)
from jadawel.core.mcp.models import MCPEndpoint


@pytest.mark.django_db
def test_composite_endpoint_creation_is_atomic_and_idempotent(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table, name="National ID")
    url = reverse("api:arabase:mcp_endpoint_protection_summaries")
    payload = {
        "name": "Protected assistant",
        "workspace_id": workspace.id,
        "protected_field_ids": [field.id],
        "confirm_empty_policy": False,
    }
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_IDEMPOTENCY_KEY": "1d75d074-58e3-43f5-a13a-b2246187fd18",
    }

    created = api_client.post(url, payload, format="json", **headers)
    replayed = api_client.post(url, payload, format="json", **headers)

    assert created.status_code == HTTP_201_CREATED
    assert replayed.status_code == HTTP_201_CREATED
    assert replayed.json() == created.json()
    body = created.json()
    assert body["id"] == MCPEndpoint.objects.get().id
    assert len(body["key"]) == 32
    assert body["protection_policy"]["protected_field_count"] == 1
    assert body["protection_policy"]["fields"][0]["id"] == field.id
    assert MCPProtectionCommand.objects.count() == 1
    assert MCPEndpoint.objects.count() == 1
    boundary = MCPProtectionLifecycleAudit.objects.get(
        event_type="POLICY_BECAME_NONEMPTY"
    )
    assert boundary.endpoint_id == body["id"]
    assert boundary.actor_id == user.id
    assert boundary.metadata == {"protected_field_count": 1}


@pytest.mark.django_db
def test_empty_policy_requires_explicit_confirmation(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    url = reverse("api:arabase:mcp_endpoint_protection_summaries")
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_IDEMPOTENCY_KEY": "empty-policy-creation-1",
    }
    payload = {
        "name": "Unprotected endpoint",
        "workspace_id": workspace.id,
        "protected_field_ids": [],
        "confirm_empty_policy": False,
    }

    rejected = api_client.post(url, payload, format="json", **headers)
    payload["confirm_empty_policy"] = True
    created = api_client.post(url, payload, format="json", **headers)

    assert rejected.status_code == HTTP_400_BAD_REQUEST
    assert created.status_code == HTTP_201_CREATED
    assert created.json()["protection_policy"]["protected_field_count"] == 0


@pytest.mark.django_db
@override_settings(FEATURE_FLAGS=[])
def test_non_empty_policy_admission_is_enabled_without_a_feature_flag(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)

    response = api_client.post(
        reverse("api:arabase:mcp_endpoint_protection_summaries"),
        {
            "name": "Default-on endpoint",
            "workspace_id": workspace.id,
            "protected_field_ids": [field.id],
            "confirm_empty_policy": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="default-on-policy-creation-1",
    )

    assert response.status_code == HTTP_201_CREATED
    assert MCPProtectedField.objects.filter(field=field).count() == 1


@pytest.mark.django_db
@override_settings(FEATURE_FLAGS=["mcp-protected-fields-staff"])
def test_staff_rollout_flag_allows_staff_but_not_regular_owners(data_fixture):
    regular = data_fixture.create_user()
    staff = data_fixture.create_user(is_staff=True)
    regular_workspace = data_fixture.create_workspace(user=regular)
    staff_workspace = data_fixture.create_workspace(user=staff)
    regular_database = data_fixture.create_database_application(
        workspace=regular_workspace
    )
    staff_database = data_fixture.create_database_application(workspace=staff_workspace)
    regular_table = data_fixture.create_database_table(database=regular_database)
    staff_table = data_fixture.create_database_table(database=staff_database)
    regular_field = data_fixture.create_text_field(table=regular_table)
    staff_field = data_fixture.create_text_field(table=staff_table)

    with pytest.raises(ValidationError):
        create_protected_mcp_endpoint(
            user=regular,
            name="Regular gated endpoint",
            workspace_id=regular_workspace.id,
            protected_field_ids=[regular_field.id],
            confirm_empty_policy=False,
            idempotency_key="regular-staff-flag-1",
        )

    created = create_protected_mcp_endpoint(
        user=staff,
        name="Staff canary endpoint",
        workspace_id=staff_workspace.id,
        protected_field_ids=[staff_field.id],
        confirm_empty_policy=False,
        idempotency_key="staff-staff-flag-1",
    )

    assert created.endpoint.user_id == staff.id
    assert created.endpoint.arabase_protection_policy.protected_fields.count() == 1


@pytest.mark.django_db
def test_composite_creation_rejects_foreign_fields_without_creating_endpoint(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    other_field = data_fixture.create_text_field()
    url = reverse("api:arabase:mcp_endpoint_protection_summaries")

    response = api_client.post(
        url,
        {
            "name": "Invalid endpoint",
            "workspace_id": workspace.id,
            "protected_field_ids": [other_field.id],
            "confirm_empty_policy": False,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="foreign-field-creation-1",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert MCPEndpoint.objects.count() == 0


@pytest.mark.django_db
def test_composite_creation_rejects_workspace_without_membership(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token()
    foreign_workspace = data_fixture.create_workspace()
    url = reverse("api:arabase:mcp_endpoint_protection_summaries")

    response = api_client.post(
        url,
        {
            "name": "Unauthorized endpoint",
            "workspace_id": foreign_workspace.id,
            "protected_field_ids": [],
            "confirm_empty_policy": True,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="foreign-workspace-creation-1",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"
    assert MCPEndpoint.objects.count() == 0


@pytest.mark.django_db
def test_composite_creation_rolls_back_endpoint_when_policy_write_fails(
    data_fixture, monkeypatch
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)

    def fail_policy_write(*args, **kwargs):
        raise RuntimeError("policy write failed")

    monkeypatch.setattr(MCPProtectedField.objects, "bulk_create", fail_policy_write)

    with pytest.raises(RuntimeError, match="policy write failed"):
        create_protected_mcp_endpoint(
            user=user,
            name="Must roll back",
            workspace_id=workspace.id,
            protected_field_ids=[field.id],
            confirm_empty_policy=False,
            idempotency_key="atomic-policy-write-1",
        )

    assert MCPEndpoint.objects.filter(name="Must roll back").exists() is False
