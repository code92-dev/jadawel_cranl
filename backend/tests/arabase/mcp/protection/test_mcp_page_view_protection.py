"""Characterization of the protected page-view MCP tools and public page surfaces.

``get_page_view`` hands a model the page template, its schema and a small row
sample.  With a protected endpoint it must withhold the raw HTML, mask
protected cells and skip the sample entirely when the view's query depends on
protected data.  The public info route and public row feed apply the same
artifact boundary for anonymous visitors.  These tests pin the observed
behaviour so a restructuring cannot change it silently.
"""

from django.test import override_settings
from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from arabase.mcp.page import services
from arabase.mcp.protection.artifact_commands import (
    approve_artifact_draft,
    submit_mcp_page_change,
)
from arabase.mcp.protection.models import (
    ArtifactAudience,
    MCPProtectedField,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.views.handler import HtmlPageRevisionHandler
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"

GET_PAGE_VIEW_KEYS = [
    "view_id",
    "name",
    "table_id",
    "is_public",
    "public_slug",
    "has_password",
    "html_bytes",
    "allow_external_resources",
    "row_limit",
    "html",
    "fields",
    "runtime_contract",
    "artifact",
    "row_count",
    "row_sample",
]

SUBMIT_RESULT_KEYS = [
    "view_id",
    "artifact_state",
    "target_generation",
    "approval_id",
    "draft_id",
    "audience",
    "endpoint_id",
    "protected_field_ids",
    "manifest",
    "view_configuration",
    "status",
    "name",
    "table_id",
    "is_public",
    "public_slug",
    "has_password",
    "html_bytes",
    "allow_external_resources",
    "row_limit",
]

UNAVAILABLE = {
    "code": "MCP_ARTIFACT_UNAVAILABLE",
    "message": (
        "This page is temporarily unavailable until its protected artifact is approved."
    ),
}

# The database vault keeps mask tokens in PostgreSQL, so no Redis is needed.
database_vault = override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)


class Page:
    def __init__(self, data_fixture):
        self.user = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(user=self.user)
        database = data_fixture.create_database_application(workspace=self.workspace)
        self.table = data_fixture.create_database_table(database=database)
        self.secret = data_fixture.create_text_field(
            table=self.table, name="Secret", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="Visible")
        self.secret2 = data_fixture.create_text_field(table=self.table, name="Secret2")
        self.protected = data_fixture.create_mcp_endpoint(
            user=self.user, workspace=self.workspace
        )
        for field in (self.secret, self.secret2):
            MCPProtectedField.objects.create(
                policy=self.protected.arabase_protection_policy, field=field
            )
        self.empty = data_fixture.create_mcp_endpoint(
            user=self.user, workspace=self.workspace
        )
        self.view = ViewHandler().create_view(
            self.user, self.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
        )
        self.table.get_model().objects.create(
            **{
                f"field_{self.secret.id}": "canary",
                f"field_{self.visible.id}": "shown",
                f"field_{self.secret2.id}": "second canary",
            }
        )

    def fresh_view(self) -> HtmlPageView:
        return HtmlPageView.objects.get(id=self.view.id)

    def read(self, endpoint, **kwargs):
        return services.get_page_view(
            self.user, self.workspace, self.view.id, endpoint=endpoint, **kwargs
        )

    def approve(self, *, audience=ArtifactAudience.AUTHENTICATED):
        pending = submit_mcp_page_change(
            user=self.user,
            endpoint=self.protected,
            view=self.fresh_view(),
            html=PAGE_V2,
            protected_field_ids=[self.secret.id],
            audience=audience,
        )
        return approve_artifact_draft(user=self.user, draft_id=pending["draft_id"])


@pytest.fixture
def page(data_fixture):
    return Page(data_fixture)


def _is_mask_envelope(value):
    return (
        isinstance(value, dict)
        and set(value) == {"$jadawelProtected"}
        and value["$jadawelProtected"]["v"] == 1
        and isinstance(value["$jadawelProtected"]["token"], str)
    )


# ---------------------------------------------------------------------------
# get_page_view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@database_vault
def test_get_page_view_with_an_empty_policy_is_unmasked(page):
    result = page.read(page.empty)

    assert list(result) == GET_PAGE_VIEW_KEYS
    assert result["html"] == PAGE_V1
    assert result["artifact"] == {"artifact_state": "unmanaged"}
    assert result["row_count"] == 1
    row = result["row_sample"][0]
    assert row["Secret"] == "canary"
    assert row["Secret2"] == "second canary"
    assert row["Visible"] == "shown"


@pytest.mark.django_db
@database_vault
def test_get_page_view_with_a_protected_endpoint_on_an_unmanaged_view(page):
    result = page.read(page.protected)

    assert list(result) == GET_PAGE_VIEW_KEYS
    assert result["html"] is None
    assert result["html_bytes"] == len(PAGE_V1)
    assert result["artifact"] == {"artifact_state": "unmanaged"}
    assert isinstance(result["row_count"], int)
    assert result["row_count"] == 1
    row = result["row_sample"][0]
    assert set(row) == {"id", "order", "Secret", "Visible", "Secret2"}
    assert _is_mask_envelope(row["Secret"])
    assert _is_mask_envelope(row["Secret2"])
    assert row["Visible"] == "shown"
    assert "canary" not in str(result)


@pytest.mark.django_db
@database_vault
def test_get_page_view_skips_rows_when_the_query_depends_on_protected_data(page):
    ViewHandler().create_filter(
        page.user, page.fresh_view(), page.secret, "equal", "canary"
    )

    result = page.read(page.protected)

    assert list(result) == GET_PAGE_VIEW_KEYS
    assert result["html"] is None
    assert result["row_count"] is None
    assert result["row_sample"] == []


@pytest.mark.django_db
@database_vault
def test_get_page_view_limits_rows_to_the_approved_projection(page):
    page.approve()

    result = page.read(page.protected)

    assert result["html"] is None
    assert result["artifact"]["artifact_state"] == "approved"
    assert result["artifact"]["protected_field_ids"] == [page.secret.id]
    assert result["row_count"] == 1
    row = result["row_sample"][0]
    assert set(row) == {"id", "order", "Secret", "Visible"}
    assert _is_mask_envelope(row["Secret"])
    assert row["Visible"] == "shown"


@pytest.mark.django_db
@database_vault
def test_get_page_view_with_a_suspended_policy(page):
    page.approve()
    MCPProtectionPolicy.objects.filter(endpoint=page.protected).update(
        lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        safe_reason_code=MCPProtectionSafeReason.WORKSPACE_SUSPENDED,
    )

    # Observed: no exception is raised.  The status read-model downgrades the
    # approval to blocked, and the failing policy load is treated as protected
    # output with a protected query dependency, so neither the HTML nor any
    # row is read.
    result = page.read(page.protected)

    assert list(result) == GET_PAGE_VIEW_KEYS
    assert result["html"] is None
    assert result["artifact"]["artifact_state"] == "blocked"
    assert result["artifact"]["approval_id"] is None
    assert result["row_count"] is None
    assert result["row_sample"] == []


@pytest.mark.django_db
@database_vault
def test_page_write_tools_with_an_endpoint_merge_the_view_summary(page):
    created = services.create_page_view(
        page.user,
        page.workspace,
        page.table.id,
        "Created",
        PAGE_V2,
        endpoint=page.protected,
        protected_field_ids=[page.secret.id],
    )
    assert list(created) == SUBMIT_RESULT_KEYS
    assert created["status"] == "pending_approval"
    created_view = HtmlPageView.objects.get(name="Created")
    assert created["view_id"] == created_view.id
    # The view is created empty; the HTML waits in the draft.
    assert created["html_bytes"] == 0

    updated = services.update_page_view(
        page.user,
        page.workspace,
        page.view.id,
        html=PAGE_V2,
        endpoint=page.protected,
        protected_field_ids=[page.secret.id],
    )
    assert list(updated) == SUBMIT_RESULT_KEYS
    assert updated["status"] == "pending_approval"
    assert updated["view_id"] == page.view.id
    assert updated["html_bytes"] == len(PAGE_V1)

    other = ViewHandler().create_view(
        page.user, page.table, HtmlPageViewType.type, name="Other", html=PAGE_V1
    )
    # The endpoint-free update path this setup used is gone: record the same
    # revision and html change directly, as that path did.
    HtmlPageRevisionHandler().snapshot(other, page.user)
    ViewHandler().update_view(page.user, other, html=PAGE_V2)
    revision_id = services.list_page_revisions(page.user, page.workspace, other.id)[0][
        "revision_id"
    ]
    restored = services.restore_page_revision(
        page.user,
        page.workspace,
        other.id,
        revision_id,
        endpoint=page.protected,
        protected_field_ids=[page.secret.id],
    )
    assert list(restored) == SUBMIT_RESULT_KEYS
    assert restored["status"] == "pending_approval"
    assert restored["view_id"] == other.id
    assert restored["html_bytes"] == len(PAGE_V2)


# ---------------------------------------------------------------------------
# Public surfaces
# ---------------------------------------------------------------------------


def public_info_url(view):
    return reverse("api:database:views:public_info", kwargs={"slug": view.slug})


def public_rows_url(view):
    return reverse(
        "api:database:views:html_page:public_rows", kwargs={"slug": view.slug}
    )


@pytest.mark.django_db
def test_public_surfaces_follow_the_public_approval(api_client, page):
    ViewHandler().update_view(page.user, page.fresh_view(), public=True)
    pending = submit_mcp_page_change(
        user=page.user,
        endpoint=page.protected,
        view=page.fresh_view(),
        html=PAGE_V2,
        protected_field_ids=[page.secret.id],
        audience=ArtifactAudience.PUBLIC,
    )
    view = page.fresh_view()

    response = api_client.get(public_info_url(view))
    assert response.status_code == 423
    assert response.json() == UNAVAILABLE
    response = api_client.get(public_rows_url(view))
    assert response.status_code == 423
    assert response.json() == UNAVAILABLE

    approve_artifact_draft(user=page.user, draft_id=pending["draft_id"])
    view = page.fresh_view()

    response = api_client.get(public_info_url(view))
    assert response.status_code == HTTP_200_OK
    assert response.json()["view"]["html"] == PAGE_V2

    response = api_client.get(public_rows_url(view))
    assert response.status_code == HTTP_200_OK
    assert set(response.json()["results"][0]) == {
        "id",
        "order",
        f"field_{page.secret.id}",
        f"field_{page.visible.id}",
    }

    response = api_client.get(public_rows_url(view), {"search": "x"})
    assert response.status_code == 423
    assert response.json() == UNAVAILABLE

    response = api_client.get(public_rows_url(view), {"search": ""})
    assert response.status_code == HTTP_200_OK
