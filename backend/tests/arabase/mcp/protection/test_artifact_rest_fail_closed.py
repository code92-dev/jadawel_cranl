"""REST artifact paths fail closed when protection cannot be proven.

A dependency cycle, a dependency missing from the graph, a broken reference on
the protected lineage or a broken field adapter makes ``protected_output_fields``
raise the MCP protocol's fixed ``SafeMCPToolError``.  Over REST every artifact
path turns it into the fixed, content-blind 423 instead of an HTTP 500, and
nothing is written.  The MCP page tools keep their own fixed MCP error.
"""

from django.test import override_settings
from django.urls import reverse

import pytest

from arabase.mcp.page import services
from arabase.mcp.protection.artifact_commands import (
    approve_artifact_draft,
    submit_mcp_page_change,
)
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactAudience,
    ArtifactDraft,
    ArtifactDraftStatus,
    MCPProtectedField,
)
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.fields.dependencies.models import FieldDependency
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.core.mcp.errors import SafeMCPToolError

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"

EXPECTED = {
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
    """An owner's page view whose primary ``secret`` field is protected."""

    def __init__(self, data_fixture):
        self.user = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(user=self.user)
        database = data_fixture.create_database_application(workspace=self.workspace)
        self.table = data_fixture.create_database_table(database=database)
        self.secret = data_fixture.create_text_field(
            table=self.table, name="Secret", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="Visible")
        self.endpoint = data_fixture.create_mcp_endpoint(
            user=self.user, workspace=self.workspace
        )
        MCPProtectedField.objects.create(
            policy=self.endpoint.arabase_protection_policy, field=self.secret
        )
        self.view = ViewHandler().create_view(
            self.user, self.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
        )
        self.table.get_model().objects.create(
            **{
                f"field_{self.secret.id}": "protected canary",
                f"field_{self.visible.id}": "shown",
            }
        )

    def fresh_view(self) -> HtmlPageView:
        return HtmlPageView.objects.get(id=self.view.id)

    def submit(self, *, audience=ArtifactAudience.AUTHENTICATED) -> dict:
        return submit_mcp_page_change(
            user=self.user,
            endpoint=self.endpoint,
            view=self.fresh_view(),
            html=PAGE_V2,
            protected_field_ids=[self.secret.id],
            audience=audience,
        )

    def approve(self, *, audience=ArtifactAudience.AUTHENTICATED) -> dict:
        pending = self.submit(audience=audience)
        return approve_artifact_draft(user=self.user, draft_id=pending["draft_id"])

    def break_graph(self):
        """Put ``secret`` on a broken reference, as a deleted dependency would."""

        FieldDependency.objects.create(
            dependant=self.secret,
            dependency=None,
            broken_reference_field_name="Missing field",
        )


@pytest.fixture
def page(data_fixture):
    return Page(data_fixture)


def _assert_fail_closed(response):
    assert response.status_code == 423
    assert response.json() == EXPECTED
    assert b"PROTECTION_UNAVAILABLE" not in response.content
    assert b"Missing field" not in response.content
    assert b"Secret" not in response.content


@pytest.mark.django_db
@database_vault
def test_authenticated_page_feed_fails_closed(api_client, page):
    page.approve()
    page.break_graph()
    api_client.force_authenticate(user=page.user)

    response = api_client.get(
        reverse("api:database:views:html_page:list", kwargs={"view_id": page.view.id}),
    )

    _assert_fail_closed(response)


@pytest.mark.django_db
@database_vault
def test_public_page_feed_and_public_info_fail_closed(api_client, page):
    ViewHandler().update_view(page.user, page.fresh_view(), public=True)
    page.submit(audience=ArtifactAudience.PUBLIC)
    page.break_graph()
    view = page.fresh_view()

    rows = api_client.get(
        reverse("api:database:views:html_page:public_rows", kwargs={"slug": view.slug})
    )
    info = api_client.get(
        reverse("api:database:views:public_info", kwargs={"slug": view.slug})
    )

    _assert_fail_closed(rows)
    _assert_fail_closed(info)


@pytest.mark.django_db
@database_vault
def test_draft_post_fails_closed_and_writes_nothing(api_client, page):
    page.break_graph()
    api_client.force_authenticate(user=page.user)

    response = api_client.post(
        reverse("api:arabase:mcp_artifact_draft"),
        {
            "endpoint_id": page.endpoint.id,
            "view_id": page.view.id,
            "html": PAGE_V2,
            "protected_field_ids": [page.secret.id],
        },
        format="json",
    )

    _assert_fail_closed(response)
    assert ArtifactDraft.objects.count() == 0
    assert page.fresh_view().html == PAGE_V1


@pytest.mark.django_db
@database_vault
def test_approve_fails_closed_and_rolls_back(api_client, page):
    pending = page.submit()
    page.break_graph()
    api_client.force_authenticate(user=page.user)

    response = api_client.post(
        reverse(
            "api:arabase:mcp_artifact_draft_approve",
            kwargs={"draft_id": pending["draft_id"]},
        ),
    )

    _assert_fail_closed(response)
    draft = ArtifactDraft.objects.get(id=pending["draft_id"])
    assert draft.status == ArtifactDraftStatus.PENDING
    assert ArtifactApproval.objects.count() == 0
    assert page.fresh_view().html == PAGE_V1


@pytest.mark.django_db
@database_vault
def test_artifact_state_fails_closed(api_client, page):
    page.approve()
    page.break_graph()
    api_client.force_authenticate(user=page.user)

    response = api_client.get(
        reverse("api:arabase:mcp_artifact_state", kwargs={"view_id": page.view.id}),
    )

    _assert_fail_closed(response)


@pytest.mark.django_db
@database_vault
def test_core_view_patch_of_a_managed_page_fails_closed(api_client, page):
    page.submit()
    page.break_graph()
    api_client.force_authenticate(user=page.user)
    drafts_before = ArtifactDraft.objects.count()

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": page.view.id}),
        {"html": PAGE_V2},
        format="json",
    )

    _assert_fail_closed(response)
    assert page.fresh_view().html == PAGE_V1
    assert ArtifactDraft.objects.count() == drafts_before


@pytest.mark.django_db
@database_vault
def test_mcp_page_tools_keep_the_fixed_mcp_error(page):
    page.break_graph()

    with pytest.raises(SafeMCPToolError):
        services.update_page_view(
            page.user,
            page.workspace,
            page.view.id,
            html=PAGE_V2,
            endpoint=page.endpoint,
            protected_field_ids=[page.secret.id],
        )
    assert page.fresh_view().html == PAGE_V1
