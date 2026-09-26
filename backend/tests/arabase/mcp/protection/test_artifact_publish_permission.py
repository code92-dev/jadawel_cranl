"""Changing page HTML needs the permission to edit the view.

``submit_mcp_page_change`` either publishes a public-only page directly
(replacing the live HTML, revoking approvals, snapshotting a revision) or files
a protected draft, which rebinds the page's governing endpoint, supersedes
pending drafts and takes the page out of public-only mode.  Every caller only
proves read access to the view before it, so the function itself checks
``UpdateViewOperationType`` before any write, on both paths.  A reader's draft
could never be approved anyway: approval also requires editing the view.
"""

from django.test import override_settings
from django.urls import reverse

import pytest

from arabase.mcp.page import services
from arabase.mcp.protection.artifact_commands import submit_mcp_page_change
from arabase.mcp.protection.models import (
    ArtifactAuditEvent,
    ArtifactDraft,
    ArtifactDraftStatus,
    HtmlPageArtifactState,
    MCPProtectedField,
)
from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST
from arabase.table_access.models import TableAccessLevel, TableGrant
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.contrib.database.views.operations import UpdateViewOperationType
from jadawel.core.exceptions import PermissionDenied, PermissionException
from jadawel.core.handler import CoreHandler

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"
PAGE_V3 = "<!doctype html><body><h1>v3</h1></body>"

PERMISSION_DENIED = {
    "error": "PERMISSION_DENIED",
    "detail": "You don't have the required permission to execute this operation.",
}

# The database vault keeps mask tokens in PostgreSQL, so no Redis is needed.
database_vault = override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)


class Page:
    """An owner's page view on a table with a ``secret`` and a ``visible`` field.

    ``endpoint`` is the owner's endpoint and protects ``secret``.
    """

    def __init__(self, data_fixture):
        self.data_fixture = data_fixture
        self.owner = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(user=self.owner)
        database = data_fixture.create_database_application(workspace=self.workspace)
        self.table = data_fixture.create_database_table(database=database)
        self.secret = data_fixture.create_text_field(
            table=self.table, name="Secret", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="Visible")
        self.endpoint = data_fixture.create_mcp_endpoint(
            user=self.owner, workspace=self.workspace
        )
        MCPProtectedField.objects.create(
            policy=self.endpoint.arabase_protection_policy, field=self.secret
        )
        self.view = ViewHandler().create_view(
            self.owner, self.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
        )

    def fresh_view(self) -> HtmlPageView:
        return HtmlPageView.objects.get(id=self.view.id)

    def make_guest(self):
        """A table guest who may read the page's view but not update it."""

        guest, token = self.data_fixture.create_user_and_token()
        workspace_user = self.data_fixture.create_user_workspace(
            workspace=self.workspace,
            user=guest,
            permissions=WORKSPACE_USER_PERMISSION_GUEST,
        )
        TableGrant.objects.create(
            workspace_user=workspace_user,
            table=self.table,
            level=TableAccessLevel.EDITOR,
        )
        return guest, token

    def make_member(self):
        """A MEMBER of the workspace who owns an endpoint with an empty policy."""

        member = self.data_fixture.create_user()
        self.data_fixture.create_user_workspace(
            workspace=self.workspace, user=member, permissions="MEMBER"
        )
        endpoint = self.data_fixture.create_mcp_endpoint(
            user=member, workspace=self.workspace
        )
        return member, endpoint


@pytest.fixture
def page(data_fixture):
    return Page(data_fixture)


def _deny_update_view_to(monkeypatch, user):
    """Make ``user`` lack UpdateView on every view, all else unchanged."""

    real_check = CoreHandler.check_permissions

    def check_permissions(self, actor, operation_name, *args, **kwargs):
        if (
            getattr(actor, "id", None) == user.id
            and operation_name == UpdateViewOperationType.type
        ):
            if kwargs.get("raise_permission_exceptions") is False:
                return False
            raise PermissionDenied(actor=actor)
        return real_check(self, actor, operation_name, *args, **kwargs)

    monkeypatch.setattr(CoreHandler, "check_permissions", check_permissions)


@pytest.mark.django_db
@database_vault
def test_read_only_guest_cannot_publish_through_the_page_tool(page):
    guest, _ = page.make_guest()
    guest_endpoint = page.data_fixture.create_mcp_endpoint(
        user=guest, workspace=page.workspace
    )
    revisions_before = page.fresh_view().revisions.count()

    with pytest.raises(PermissionException):
        services.update_page_view(
            guest,
            page.workspace,
            page.view.id,
            html=PAGE_V2,
            endpoint=guest_endpoint,
        )

    view = page.fresh_view()
    assert view.html == PAGE_V1
    assert not HtmlPageArtifactState.objects.filter(view_id=view.id).exists()
    assert not ArtifactAuditEvent.objects.filter(
        event_type="public_only_published"
    ).exists()
    assert view.revisions.count() == revisions_before


@pytest.mark.django_db
@database_vault
def test_read_only_guest_cannot_publish_through_the_view_patch(api_client, page):
    published = submit_mcp_page_change(
        user=page.owner,
        endpoint=page.endpoint,
        view=page.fresh_view(),
        html=PAGE_V2,
        protected_field_ids=[],
    )
    assert published["status"] == "published"
    state = HtmlPageArtifactState.objects.get(view_id=page.view.id)
    assert state.endpoint_id == page.endpoint.id
    assert state.public_only is True
    assert not ArtifactDraft.objects.filter(view_id=page.view.id).exists()
    generation_before = state.target_generation
    _, token = page.make_guest()

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": page.view.id}),
        {"html": PAGE_V3},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == 401, response.content
    assert response.json() == PERMISSION_DENIED
    assert page.fresh_view().html == PAGE_V2
    state.refresh_from_db()
    assert state.target_generation == generation_before
    assert state.endpoint_id == page.endpoint.id
    assert state.public_only is True
    assert not ArtifactDraft.objects.filter(view_id=page.view.id).exists()


@pytest.mark.django_db
@database_vault
def test_publish_through_the_draft_endpoint_requires_update_view(
    api_client, monkeypatch, page
):
    member, member_endpoint = page.make_member()
    _deny_update_view_to(monkeypatch, member)
    api_client.force_authenticate(user=member)

    response = api_client.post(
        reverse("api:arabase:mcp_artifact_draft"),
        {
            "endpoint_id": member_endpoint.id,
            "view_id": page.view.id,
            "html": PAGE_V2,
            "protected_field_ids": [],
        },
        format="json",
    )

    assert response.status_code == 401, response.content
    assert response.json() == PERMISSION_DENIED
    assert page.fresh_view().html == PAGE_V1
    assert not HtmlPageArtifactState.objects.filter(view_id=page.view.id).exists()
    assert not ArtifactAuditEvent.objects.filter(
        event_type="public_only_published"
    ).exists()


@pytest.mark.django_db
@database_vault
def test_read_only_callers_cannot_submit_a_protected_draft(
    api_client, monkeypatch, page
):
    published = submit_mcp_page_change(
        user=page.owner,
        endpoint=page.endpoint,
        view=page.fresh_view(),
        html=PAGE_V2,
        protected_field_ids=[],
    )
    assert published["status"] == "published"
    owner_draft = submit_mcp_page_change(
        user=page.owner,
        endpoint=page.endpoint,
        view=page.fresh_view(),
        html=PAGE_V3,
        protected_field_ids=[page.secret.id],
    )
    assert owner_draft["status"] == "pending_approval"
    state = HtmlPageArtifactState.objects.get(view_id=page.view.id)
    # The owner's pending draft took the page out of public-only mode; put it
    # back so a reader flipping it again would be visible.
    state.public_only = True
    state.save(update_fields=["public_only"])
    drafts_before = set(ArtifactDraft.objects.values_list("id", "status"))

    # Through the core view PATCH, which reroutes a managed page's HTML edit.
    guest, token = page.make_guest()
    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": page.view.id}),
        {"html": PAGE_V1},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 401, response.content
    assert response.json() == PERMISSION_DENIED

    # Through the draft endpoint, with the reader's own protecting endpoint.
    member, member_endpoint = page.make_member()
    MCPProtectedField.objects.create(
        policy=member_endpoint.arabase_protection_policy, field=page.secret
    )
    _deny_update_view_to(monkeypatch, member)
    api_client.force_authenticate(user=member)
    response = api_client.post(
        reverse("api:arabase:mcp_artifact_draft"),
        {
            "endpoint_id": member_endpoint.id,
            "view_id": page.view.id,
            "html": PAGE_V1,
            "protected_field_ids": [page.secret.id],
        },
        format="json",
    )
    assert response.status_code == 401, response.content
    assert response.json() == PERMISSION_DENIED

    # Nothing about the live page moved: governing endpoint, public-only mode,
    # the owner's pending draft, and the HTML.
    state.refresh_from_db()
    assert state.endpoint_id == page.endpoint.id
    assert state.public_only is True
    assert set(ArtifactDraft.objects.values_list("id", "status")) == drafts_before
    assert ArtifactDraft.objects.get(id=owner_draft["draft_id"]).status == (
        ArtifactDraftStatus.PENDING
    )
    assert not ArtifactDraft.objects.filter(submitted_by__in=[guest, member]).exists()
    assert page.fresh_view().html == PAGE_V2
