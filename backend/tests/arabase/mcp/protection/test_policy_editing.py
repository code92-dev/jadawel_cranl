from django.conf import settings
from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectionEditCommand,
    MCPProtectionLifecycleAudit,
)


def _url(endpoint):
    return reverse(
        "api:arabase:mcp_protection_policy", kwargs={"endpoint_id": endpoint.id}
    )


def test_policy_replace_cors_preflight_allows_idempotency_header():
    allowed_headers = {header.lower() for header in settings.CORS_ALLOW_HEADERS}
    assert "idempotency-key" in allowed_headers


@pytest.mark.django_db
def test_policy_replace_is_revisioned_and_idempotent(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    first = data_fixture.create_text_field(table=table, name="First")
    second = data_fixture.create_text_field(table=table, name="Second")
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=first
    )
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_IDEMPOTENCY_KEY": "policy-edit-0001",
    }
    payload = {
        "protected_field_ids": [second.id],
        "expected_revision": 1,
        "confirm_remove_field_ids": [first.id],
    }

    response = api_client.patch(_url(endpoint), payload, format="json", **headers)
    replay = api_client.patch(_url(endpoint), payload, format="json", **headers)

    assert response.status_code == HTTP_200_OK
    assert replay.status_code == HTTP_200_OK
    assert response.json() == replay.json()
    assert response.json()["revision"] == 2
    assert list(
        MCPProtectedField.objects.filter(
            policy=endpoint.arabase_protection_policy
        ).values_list("field_id", flat=True)
    ) == [second.id]
    assert MCPProtectionEditCommand.objects.count() == 1


@pytest.mark.django_db
def test_first_non_empty_policy_edit_records_forward_only_rollout_boundary(
    data_fixture,
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table, name="First")
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)

    from arabase.mcp.protection.policy_commands import replace_mcp_protection_policy

    replace_mcp_protection_policy(
        user=user,
        endpoint_id=endpoint.id,
        protected_field_ids=[field.id],
        expected_revision=1,
        confirm_remove_field_ids=[],
        idempotency_key="policy-boundary-1",
    )

    boundary = MCPProtectionLifecycleAudit.objects.get(
        endpoint=endpoint, event_type="POLICY_BECAME_NONEMPTY"
    )
    assert boundary.policy_revision == 2
    assert boundary.access_generation == 2
    assert boundary.metadata == {"protected_field_count": 1}


@pytest.mark.django_db
def test_policy_replace_rejects_stale_revision_and_unconfirmed_removal(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    headers = {
        "HTTP_AUTHORIZATION": f"JWT {token}",
        "HTTP_IDEMPOTENCY_KEY": "policy-edit-0002",
    }

    unconfirmed = api_client.patch(
        _url(endpoint),
        {
            "protected_field_ids": [],
            "expected_revision": 1,
            "confirm_remove_field_ids": [],
        },
        format="json",
        **headers,
    )
    stale = api_client.patch(
        _url(endpoint),
        {
            "protected_field_ids": [field.id],
            "expected_revision": 99,
            "confirm_remove_field_ids": [],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_IDEMPOTENCY_KEY="policy-edit-0003",
    )

    assert unconfirmed.status_code == HTTP_400_BAD_REQUEST
    assert stale.status_code == HTTP_409_CONFLICT
