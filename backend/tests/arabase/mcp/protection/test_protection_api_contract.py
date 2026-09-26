"""Characterization of the MCP protection HTTP contract.

These tests pin the observed status codes, bodies, error codes and check order
of the protection policy, readiness, summary and artifact routes.  An unknown
endpoint, or one owned by someone else, is a 404 on every policy route and on
the artifact draft POST, after the request body has been validated.  The
artifact draft route answers 201 only when the request created a pending
draft, and 200 for a publish.  The idempotency fingerprints are pinned as
literal digests.
"""

from django.test import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from arabase.mcp.protection import policy_commands
from arabase.mcp.protection.artifact_commands import submit_mcp_page_change
from arabase.mcp.protection.models import (
    ArtifactAudience,
    ArtifactDraft,
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionEditCommand,
    MCPProtectionLifecycleAudit,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.models import WORKSPACE_USER_PERMISSION_ADMIN

UNKNOWN_ENDPOINT_ID = 999999
ENDPOINT_NOT_FOUND = {
    "error": "ERROR_MCP_ENDPOINT_DOES_NOT_EXIST",
    "detail": "The requested MCP endpoint does not exist.",
}
# Whole-request query counts for a policy with three protected fields in two
# tables. The responses prefetch the relations once with their field, table,
# database and workspace (before: PATCH 31, reactivate 35, GET 12).
PATCH_QUERIES = 20
REACTIVATE_QUERIES = 24
GET_QUERIES = 7
PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"

# The database vault keeps mask tokens in PostgreSQL, so no Redis is needed.
database_vault = override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)


def policy_url(endpoint_id):
    return reverse(
        "api:arabase:mcp_protection_policy", kwargs={"endpoint_id": endpoint_id}
    )


def readiness_url():
    return reverse("api:arabase:mcp_protection_readiness")


def summaries_url():
    return reverse("api:arabase:mcp_endpoint_protection_summaries")


def draft_url():
    return reverse("api:arabase:mcp_artifact_draft")


def revoke_url(view_id):
    return reverse("api:arabase:mcp_artifact_revoke", kwargs={"view_id": view_id})


class Owner:
    """One owner with a workspace, a table with two fields and an endpoint."""

    def __init__(self, data_fixture):
        self.user = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(user=self.user)
        self.database = data_fixture.create_database_application(
            workspace=self.workspace, name="Customer records"
        )
        self.table = data_fixture.create_database_table(
            database=self.database, name="Customers"
        )
        self.secret = data_fixture.create_text_field(
            table=self.table, name="National ID", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="City")
        self.endpoint = data_fixture.create_mcp_endpoint(
            user=self.user, workspace=self.workspace
        )

    @property
    def policy(self) -> MCPProtectionPolicy:
        return MCPProtectionPolicy.objects.get(endpoint=self.endpoint)

    def protect_secret(self):
        MCPProtectedField.objects.create(
            policy=self.endpoint.arabase_protection_policy, field=self.secret
        )


@pytest.fixture
def owner(data_fixture):
    return Owner(data_fixture)


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_readiness_is_ready_without_protected_fields(api_client, owner):
    response = api_client.get(readiness_url())

    assert response.status_code == HTTP_200_OK
    assert response.json() == {"ready": True, "reason": ""}


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_VAULT="redis",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)
def test_readiness_is_unavailable_for_an_unconfigured_redis_vault(api_client, owner):
    owner.protect_secret()

    response = api_client.get(readiness_url())

    assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        "ready": False,
        "reason": "PROTECTION_REDIS_UNAVAILABLE",
    }


# ---------------------------------------------------------------------------
# Policy routes: unknown endpoints and check order
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@database_vault
def test_unknown_endpoint_is_not_found_on_policy_writes_and_artifact_draft(
    api_client, data_fixture, owner
):
    view = ViewHandler().create_view(
        owner.user, owner.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
    )
    api_client.force_authenticate(user=owner.user)
    replace_body = {"protected_field_ids": [], "expected_revision": 1}

    patched = api_client.patch(
        policy_url(UNKNOWN_ENDPOINT_ID),
        replace_body,
        format="json",
        HTTP_IDEMPOTENCY_KEY="unmapped-patch-1",
    )
    put = api_client.put(
        policy_url(UNKNOWN_ENDPOINT_ID),
        replace_body,
        format="json",
        HTTP_IDEMPOTENCY_KEY="unmapped-put-1",
    )
    reactivated = api_client.post(
        policy_url(UNKNOWN_ENDPOINT_ID),
        {"expected_revision": 1},
        format="json",
    )
    drafted = api_client.post(
        draft_url(),
        {
            "endpoint_id": UNKNOWN_ENDPOINT_ID,
            "view_id": view.id,
            "html": PAGE_V2,
        },
        format="json",
    )

    for response in (patched, put, reactivated, drafted):
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json() == ENDPOINT_NOT_FOUND

    # Another workspace member's endpoint is not found either, so its
    # existence does not leak.
    other = data_fixture.create_user()
    data_fixture.create_user_workspace(
        workspace=owner.workspace, user=other, permissions="MEMBER"
    )
    foreign = data_fixture.create_mcp_endpoint(user=other, workspace=owner.workspace)
    assert owner.workspace.workspaceuser_set.filter(user=other).exists()
    foreign_policy = MCPProtectionPolicy.objects.get(endpoint=foreign)

    foreign_patch = api_client.patch(
        policy_url(foreign.id),
        {"protected_field_ids": [], "expected_revision": foreign_policy.revision},
        format="json",
        HTTP_IDEMPOTENCY_KEY="foreign-patch-1",
    )
    foreign_draft = api_client.post(
        draft_url(),
        {"endpoint_id": foreign.id, "view_id": view.id, "html": PAGE_V2},
        format="json",
    )

    for response in (foreign_patch, foreign_draft):
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json() == ENDPOINT_NOT_FOUND
    foreign_policy_after = MCPProtectionPolicy.objects.get(endpoint=foreign)
    assert foreign_policy_after.revision == foreign_policy.revision
    assert not MCPProtectionEditCommand.objects.filter(
        policy=foreign_policy_after
    ).exists()
    assert not MCPProtectionEditCommand.objects.exists()
    assert not ArtifactDraft.objects.exists()


@pytest.mark.django_db
def test_unknown_endpoint_still_validates_the_body_first(api_client, owner):
    api_client.force_authenticate(user=owner.user)

    patched = api_client.patch(
        policy_url(UNKNOWN_ENDPOINT_ID),
        {"protected_field_ids": []},
        format="json",
        HTTP_IDEMPOTENCY_KEY="body-first-patch-1",
    )
    reactivated = api_client.post(policy_url(UNKNOWN_ENDPOINT_ID), {}, format="json")
    drafted = api_client.post(
        draft_url(),
        {"endpoint_id": UNKNOWN_ENDPOINT_ID, "view_id": 1},
        format="json",
    )

    assert patched.status_code == HTTP_400_BAD_REQUEST
    assert patched.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert reactivated.status_code == HTTP_400_BAD_REQUEST
    assert reactivated.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert drafted.status_code == HTTP_400_BAD_REQUEST
    assert drafted.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_invalid_idempotency_key_is_checked_before_the_endpoint(api_client, owner):
    api_client.force_authenticate(user=owner.user)

    response = api_client.patch(
        policy_url(UNKNOWN_ENDPOINT_ID),
        {"protected_field_ids": [], "expected_revision": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY="short",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "idempotency_key" in response.json()
    assert response.json() == {
        "idempotency_key": "Provide an 8 to 128 character Idempotency-Key."
    }


@pytest.mark.django_db
@database_vault
def test_put_behaves_like_patch_and_replays_the_same_body(api_client, owner):
    api_client.force_authenticate(user=owner.user)
    body = {"protected_field_ids": [owner.secret.id], "expected_revision": 1}

    first = api_client.put(
        policy_url(owner.endpoint.id),
        body,
        format="json",
        HTTP_IDEMPOTENCY_KEY="policy-put-0001",
    )
    replay = api_client.put(
        policy_url(owner.endpoint.id),
        body,
        format="json",
        HTTP_IDEMPOTENCY_KEY="policy-put-0001",
    )

    assert first.status_code == HTTP_200_OK
    assert replay.status_code == HTTP_200_OK
    assert replay.json() == first.json()
    assert first.json()["revision"] == 2


@pytest.mark.django_db
@database_vault
def test_patch_and_get_return_the_exact_policy_body(api_client, owner):
    api_client.force_authenticate(user=owner.user)

    patched = api_client.patch(
        policy_url(owner.endpoint.id),
        {"protected_field_ids": [owner.secret.id], "expected_revision": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY="policy-exact-0001",
    )
    fetched = api_client.get(policy_url(owner.endpoint.id))

    assert patched.status_code == HTTP_200_OK
    assert fetched.status_code == HTTP_200_OK
    body = patched.json()
    expected = {
        "endpoint_id": owner.endpoint.id,
        "revision": 2,
        "lifecycle_status": "active",
        "safe_reason_code": "",
        "protected_field_count": 1,
        "fields": [
            {
                "id": owner.secret.id,
                "state": "active",
                "safe_reason_code": "",
                "name": "National ID",
                "type": "text",
                "table": {"id": owner.table.id, "name": "Customers"},
                "database": {"id": owner.database.id, "name": "Customer records"},
            }
        ],
        "created_on": body["created_on"],
        "updated_on": body["updated_on"],
    }
    assert body == expected
    assert fetched.json() == expected
    assert list(body) == list(expected)


# ---------------------------------------------------------------------------
# Reactivate
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reactivate_on_an_active_policy_returns_it_unchanged(api_client, owner):
    owner.protect_secret()
    api_client.force_authenticate(user=owner.user)

    response = api_client.post(
        policy_url(owner.endpoint.id), {"expected_revision": 1}, format="json"
    )
    fetched = api_client.get(policy_url(owner.endpoint.id))

    assert response.status_code == HTTP_200_OK
    assert response.json() == fetched.json()
    assert response.json()["revision"] == 1
    assert response.json()["lifecycle_status"] == "active"


@pytest.mark.django_db
def test_reactivate_with_a_stale_revision_is_a_revision_conflict(api_client, owner):
    api_client.force_authenticate(user=owner.user)

    response = api_client.post(
        policy_url(owner.endpoint.id), {"expected_revision": 7}, format="json"
    )

    assert response.status_code == HTTP_409_CONFLICT
    assert response.json() == {
        "error": "MCP_PROTECTION_REVISION_CONFLICT",
        "detail": "",
    }


@pytest.mark.django_db
def test_reactivate_with_an_unvalidated_field_is_not_ready(api_client, owner):
    owner.protect_secret()
    # Trashing the protected field blocks the policy; reactivation then fails
    # the field validation step.
    owner.secret.trashed = True
    owner.secret.save(update_fields=["trashed"])
    policy = owner.policy
    assert policy.lifecycle_status == MCPProtectionLifecycleStatus.PROTECTION_BLOCKED
    api_client.force_authenticate(user=owner.user)

    response = api_client.post(
        policy_url(owner.endpoint.id),
        {"expected_revision": policy.revision},
        format="json",
    )

    assert response.status_code == HTTP_409_CONFLICT
    assert response.json() == {"error": "MCP_PROTECTION_NOT_READY", "detail": ""}
    assert owner.policy.revision == policy.revision


@pytest.mark.django_db
def test_reactivate_by_an_owner_who_left_is_refused_by_get_endpoint(api_client, owner):
    # The membership branch of reactivation is unreachable over HTTP:
    # get_endpoint's permission check refuses a non-member first.
    owner.protect_secret()
    owner.workspace.workspaceuser_set.get(user=owner.user).delete()
    policy = owner.policy
    assert policy.lifecycle_status == MCPProtectionLifecycleStatus.SUSPENDED
    api_client.force_authenticate(user=owner.user)

    response = api_client.post(
        policy_url(owner.endpoint.id),
        {"expected_revision": policy.revision},
        format="json",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error": "PERMISSION_DENIED",
        "detail": "You don't have the required permission to execute this operation.",
    }
    assert owner.policy.revision == policy.revision


# ---------------------------------------------------------------------------
# Response query shape
# ---------------------------------------------------------------------------


def _three_fields_in_two_tables(data_fixture, owner):
    """Return the owner's two fields plus one field of a second table."""

    orders = data_fixture.create_database_table(database=owner.database, name="Orders")
    amount = data_fixture.create_text_field(table=orders, name="Amount", primary=True)
    return orders, [owner.secret, owner.visible, amount]


def _field_body(field, table, database, state="active"):
    return {
        "id": field.id,
        "state": state,
        "safe_reason_code": "",
        "name": field.name,
        "type": "text",
        "table": {"id": table.id, "name": table.name},
        "database": {"id": database.id, "name": database.name},
    }


@pytest.mark.django_db
@database_vault
def test_patch_response_query_count_with_three_fields_in_two_tables(
    api_client, data_fixture, owner, django_assert_num_fork_queries
):
    orders, fields = _three_fields_in_two_tables(data_fixture, owner)
    api_client.force_authenticate(user=owner.user)

    with django_assert_num_fork_queries(PATCH_QUERIES):
        response = api_client.patch(
            policy_url(owner.endpoint.id),
            {
                "protected_field_ids": [field.id for field in fields],
                "expected_revision": 1,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="policy-queries-0001",
        )

    assert response.status_code == HTTP_200_OK
    body = response.json()
    expected = {
        "endpoint_id": owner.endpoint.id,
        "revision": 2,
        "lifecycle_status": "active",
        "safe_reason_code": "",
        "protected_field_count": 3,
        "fields": [
            _field_body(owner.secret, owner.table, owner.database),
            _field_body(owner.visible, owner.table, owner.database),
            _field_body(fields[2], orders, owner.database),
        ],
        "created_on": body["created_on"],
        "updated_on": body["updated_on"],
    }
    assert body == expected
    assert list(body) == list(expected)


@pytest.mark.django_db
def test_get_response_query_count_with_three_fields_in_two_tables(
    api_client, data_fixture, owner, django_assert_num_fork_queries
):
    orders, fields = _three_fields_in_two_tables(data_fixture, owner)
    policy = owner.endpoint.arabase_protection_policy
    MCPProtectedField.objects.bulk_create(
        [MCPProtectedField(policy=policy, field=field) for field in fields]
    )
    api_client.force_authenticate(user=owner.user)

    with django_assert_num_fork_queries(GET_QUERIES):
        response = api_client.get(policy_url(owner.endpoint.id))

    assert response.status_code == HTTP_200_OK
    body = response.json()
    expected = {
        "endpoint_id": owner.endpoint.id,
        "revision": 1,
        "lifecycle_status": "active",
        "safe_reason_code": "",
        "protected_field_count": 3,
        "fields": [
            _field_body(owner.secret, owner.table, owner.database),
            _field_body(owner.visible, owner.table, owner.database),
            _field_body(fields[2], orders, owner.database),
        ],
        "created_on": body["created_on"],
        "updated_on": body["updated_on"],
    }
    assert body == expected
    assert list(body) == list(expected)


@pytest.mark.django_db
@database_vault
def test_reactivate_response_query_count_with_three_fields_in_two_tables(
    api_client, data_fixture, owner, django_assert_num_fork_queries
):
    orders, fields = _three_fields_in_two_tables(data_fixture, owner)
    policy = owner.endpoint.arabase_protection_policy
    MCPProtectedField.objects.bulk_create(
        [MCPProtectedField(policy=policy, field=field) for field in fields]
    )
    MCPProtectedField.objects.filter(policy=policy, field=fields[2]).update(
        state=MCPProtectedFieldState.SUSPENDED,
        safe_reason_code=MCPProtectionSafeReason.POLICY_RELATION_INVALID,
    )
    MCPProtectionPolicy.objects.filter(id=policy.id).update(
        lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        safe_reason_code=MCPProtectionSafeReason.MEMBERSHIP_CHANGED,
    )
    revision = owner.policy.revision
    api_client.force_authenticate(user=owner.user)

    with django_assert_num_fork_queries(REACTIVATE_QUERIES):
        response = api_client.post(
            policy_url(owner.endpoint.id),
            {"expected_revision": revision},
            format="json",
        )

    assert response.status_code == HTTP_200_OK
    body = response.json()
    expected = {
        "endpoint_id": owner.endpoint.id,
        # The key rotation adds one through the signal, then reactivation one.
        "revision": revision + 2,
        "lifecycle_status": "active",
        "safe_reason_code": "",
        "protected_field_count": 3,
        "fields": [
            _field_body(owner.secret, owner.table, owner.database),
            _field_body(owner.visible, owner.table, owner.database),
            _field_body(fields[2], orders, owner.database),
        ],
        "created_on": body["created_on"],
        "updated_on": body["updated_on"],
    }
    assert body == expected
    assert list(body) == list(expected)


# ---------------------------------------------------------------------------
# DELETE (ownerless admin delete)
# ---------------------------------------------------------------------------


def _admin(data_fixture, workspace):
    admin = data_fixture.create_user()
    data_fixture.create_user_workspace(
        user=admin, workspace=workspace, permissions=WORKSPACE_USER_PERMISSION_ADMIN
    )
    return admin


@pytest.mark.django_db
def test_delete_of_an_unknown_endpoint_is_not_found(api_client, owner):
    api_client.force_authenticate(user=owner.user)

    response = api_client.delete(policy_url(UNKNOWN_ENDPOINT_ID))

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_MCP_ENDPOINT_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_delete_refusals_carry_their_exact_texts(api_client, data_fixture, owner):
    owner.protect_secret()
    member = data_fixture.create_user()
    data_fixture.create_user_workspace(
        user=member, workspace=owner.workspace, permissions="MEMBER"
    )
    admin = _admin(data_fixture, owner.workspace)

    api_client.force_authenticate(user=member)
    non_admin = api_client.delete(policy_url(owner.endpoint.id))

    api_client.force_authenticate(user=admin)
    active_policy = api_client.delete(policy_url(owner.endpoint.id))

    # Trashing the protected field blocks the policy while the owner stays.
    owner.secret.trashed = True
    owner.secret.save(update_fields=["trashed"])
    assert owner.policy.lifecycle_status == (
        MCPProtectionLifecycleStatus.PROTECTION_BLOCKED
    )
    owner_present = api_client.delete(policy_url(owner.endpoint.id))

    assert non_admin.status_code == HTTP_403_FORBIDDEN
    assert non_admin.json() == {
        "detail": "Only a workspace administrator may delete this endpoint."
    }
    assert active_policy.status_code == HTTP_403_FORBIDDEN
    assert active_policy.json() == {
        "detail": "Only a suspended or blocked ownerless endpoint may be deleted."
    }
    assert owner_present.status_code == HTTP_403_FORBIDDEN
    assert owner_present.json() == {
        "detail": "The endpoint owner must be inactive or absent from the workspace."
    }
    assert MCPEndpoint.objects.filter(id=owner.endpoint.id).exists()
    assert not MCPProtectionLifecycleAudit.objects.filter(
        event_type="ownerless_admin_delete"
    ).exists()


@pytest.mark.django_db
def test_admin_deletes_an_ownerless_suspended_endpoint(api_client, data_fixture, owner):
    owner.protect_secret()
    owner.workspace.workspaceuser_set.get(user=owner.user).delete()
    policy = owner.policy
    assert policy.lifecycle_status == MCPProtectionLifecycleStatus.SUSPENDED
    admin = _admin(data_fixture, owner.workspace)
    api_client.force_authenticate(user=admin)

    response = api_client.delete(policy_url(owner.endpoint.id))

    assert response.status_code == HTTP_204_NO_CONTENT
    assert response.content == b""
    assert not MCPEndpoint.objects.filter(id=owner.endpoint.id).exists()
    audit = MCPProtectionLifecycleAudit.objects.get(event_type="ownerless_admin_delete")
    assert audit.endpoint_id is None
    assert audit.actor_id == admin.id
    assert audit.from_lifecycle_status == MCPProtectionLifecycleStatus.SUSPENDED
    assert audit.to_lifecycle_status == "deleted"
    assert audit.reason_code == MCPProtectionSafeReason.MEMBERSHIP_CHANGED
    assert audit.policy_revision == policy.revision
    assert audit.access_generation == policy.access_generation
    assert audit.metadata == {"endpoint_id": owner.endpoint.id}


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_summaries_show_own_endpoints_and_ownerless_suspended_ones_to_admins(
    api_client, data_fixture, owner
):
    # owner.user created the workspace, so it is a workspace admin.
    member = data_fixture.create_user()
    data_fixture.create_user_workspace(
        user=member, workspace=owner.workspace, permissions="MEMBER"
    )
    member_first = data_fixture.create_mcp_endpoint(
        user=member, workspace=owner.workspace
    )
    member_second = data_fixture.create_mcp_endpoint(
        user=member, workspace=owner.workspace
    )

    leaver = data_fixture.create_user()
    data_fixture.create_user_workspace(user=leaver, workspace=owner.workspace)
    suspended = data_fixture.create_mcp_endpoint(user=leaver, workspace=owner.workspace)
    other_leaver = data_fixture.create_user()
    data_fixture.create_user_workspace(user=other_leaver, workspace=owner.workspace)
    ownerless_active = data_fixture.create_mcp_endpoint(
        user=other_leaver, workspace=owner.workspace
    )
    owner.workspace.workspaceuser_set.filter(user__in=[leaver, other_leaver]).delete()
    assert (
        MCPProtectionPolicy.objects.get(endpoint=suspended).lifecycle_status
        == MCPProtectionLifecycleStatus.SUSPENDED
    )
    # An ownerless endpoint whose policy is ACTIVE stays hidden from admins.
    MCPProtectionPolicy.objects.filter(endpoint=ownerless_active).update(
        lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
        safe_reason_code=MCPProtectionSafeReason.NONE,
    )

    api_client.force_authenticate(user=member)
    member_ids = {row["endpoint_id"] for row in api_client.get(summaries_url()).json()}
    api_client.force_authenticate(user=owner.user)
    admin_rows = api_client.get(summaries_url()).json()

    assert member_ids == {member_first.id, member_second.id}
    assert {row["endpoint_id"] for row in admin_rows} == {
        owner.endpoint.id,
        suspended.id,
    }
    suspended_row = next(
        row for row in admin_rows if row["endpoint_id"] == suspended.id
    )
    assert suspended_row == {
        "endpoint_id": suspended.id,
        "name": suspended.name,
        "workspace_id": owner.workspace.id,
        "workspace_name": owner.workspace.name,
        "protected_field_count": 0,
        "lifecycle_status": "suspended",
        "safe_reason_code": "MEMBERSHIP_CHANGED",
    }


# ---------------------------------------------------------------------------
# Artifact routes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@database_vault
def test_artifact_draft_is_201_only_when_a_draft_is_created(
    api_client, data_fixture, owner
):
    owner.protect_secret()
    empty = data_fixture.create_mcp_endpoint(user=owner.user, workspace=owner.workspace)
    view = ViewHandler().create_view(
        owner.user, owner.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
    )
    api_client.force_authenticate(user=owner.user)

    # A public-only publish with no pending draft answers 200.
    public_only = api_client.post(
        draft_url(),
        {"endpoint_id": empty.id, "view_id": view.id, "html": PAGE_V2},
        format="json",
    )
    assert public_only.status_code == HTTP_200_OK
    assert public_only.json()["status"] == "published"
    assert public_only.json()["draft_id"] is None

    # A protected draft is created with 201.
    protected = api_client.post(
        draft_url(),
        {
            "endpoint_id": owner.endpoint.id,
            "view_id": view.id,
            "html": PAGE_V1,
            "protected_field_ids": [owner.secret.id],
        },
        format="json",
    )
    assert protected.status_code == HTTP_201_CREATED
    assert protected.json()["status"] == "pending_approval"
    draft_id = protected.json()["draft_id"]
    assert draft_id

    # Another endpoint's public-only publish creates no draft, so it answers
    # 200 even though the summary still reports the pending draft id.
    published = api_client.post(
        draft_url(),
        {"endpoint_id": empty.id, "view_id": view.id, "html": PAGE_V2},
        format="json",
    )
    assert published.status_code == HTTP_200_OK
    assert published.json()["status"] == "published"
    assert published.json()["draft_id"] == draft_id


@pytest.mark.django_db
@database_vault
def test_artifact_revoke_route(api_client, data_fixture, owner):
    owner.protect_secret()
    view = ViewHandler().create_view(
        owner.user, owner.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
    )
    submit_mcp_page_change(
        user=owner.user,
        endpoint=owner.endpoint,
        view=view,
        html=PAGE_V2,
        protected_field_ids=[owner.secret.id],
        audience=ArtifactAudience.AUTHENTICATED,
    )
    stranger = data_fixture.create_user()
    data_fixture.create_user_workspace(user=stranger, workspace=owner.workspace)

    api_client.force_authenticate(user=owner.user)
    unknown = api_client.post(revoke_url(UNKNOWN_ENDPOINT_ID), {}, format="json")
    api_client.force_authenticate(user=stranger)
    forbidden = api_client.post(revoke_url(view.id), {}, format="json")
    api_client.force_authenticate(user=owner.user)
    revoked = api_client.post(revoke_url(view.id), {}, format="json")

    assert unknown.status_code == HTTP_404_NOT_FOUND
    assert unknown.json()["error"] == "ERROR_HTML_PAGE_DOES_NOT_EXIST"
    assert forbidden.status_code == HTTP_403_FORBIDDEN
    assert forbidden.json() == {
        "detail": "Only the artifact endpoint owner may revoke it."
    }
    assert revoked.status_code == HTTP_200_OK
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["view_id"] == view.id


# ---------------------------------------------------------------------------
# Idempotency fingerprints
# ---------------------------------------------------------------------------


def test_create_request_fingerprint_is_byte_stable_for_arabic_input():
    fingerprint = policy_commands._request_fingerprint(
        {
            "confirm_empty_policy": False,
            "name": "جداول المبيعات",
            "protected_field_ids": sorted([3, 1]),
            "workspace_id": 7,
        }
    )

    assert fingerprint == (
        "6d8bf7b526252e5d4d0bf501cfd350b51257b4f20caf725228a536533ba72d68"
    )


def test_edit_request_fingerprint_is_byte_stable():
    fingerprint = policy_commands._request_fingerprint(
        {
            "confirm_remove_field_ids": sorted([4]),
            "endpoint_id": 5,
            "expected_revision": 3,
            "protected_field_ids": sorted([9, 2]),
        }
    )

    assert fingerprint == (
        "98f55c7849d582b090fd4b7035116ee0a230c1e2ebbc36329250eba894fd8544"
    )
