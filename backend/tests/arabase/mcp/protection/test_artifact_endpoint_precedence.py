"""Characterization of which endpoint each artifact code path resolves.

A page's artifact state, its drafts and its approvals can each point at a
different MCP endpoint, and every call site picks among them in its own order.
These tests pin the observed precedence of each call site, the fail-closed
path for a duplicated page whose source endpoint was deleted, and the fact that
ordinary view-setting edits never revoke an approval (no view-signal receiver
exists; the runtime fingerprints block a stale approval instead).  They
describe current behaviour, so a restructuring cannot change any of it
silently.
"""

from django.urls import reverse
from django.utils import timezone

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
)

from arabase.mcp.protection.artifact_boundary import (
    ArtifactExposureBlocked,
    _feed_query_endpoint,
    artifact_status_for_view,
    page_feed_field_ids,
    page_runtime_access,
)
from arabase.mcp.protection.artifact_commands import (
    approve_artifact_draft,
    revoke_artifact,
    submit_mcp_page_change,
)
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactAudience,
    ArtifactAuditEvent,
    ArtifactDraft,
    ArtifactDraftStatus,
    HtmlPageArtifactState,
    MCPProtectedField,
)
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.contrib.database.views.models import ViewFilter

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"
PAGE_V3 = "<!doctype html><body><h1>v3</h1></body>"
PAGE_V4 = "<!doctype html><body><h1>v4</h1></body>"


class Setup:
    """Workspace W with user1/user2, table T and endpoints A, B and C."""

    def __init__(self, data_fixture):
        self.user1 = data_fixture.create_user()
        self.user2 = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(users=[self.user1, self.user2])
        database = data_fixture.create_database_application(workspace=self.workspace)
        self.table = data_fixture.create_database_table(database=database)
        self.secret = data_fixture.create_text_field(
            table=self.table, name="Secret", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="Visible")
        # A: user1, protects Secret.  B: user2, empty policy.  C: user1,
        # protects Secret.
        self.endpoint_a = data_fixture.create_mcp_endpoint(
            user=self.user1, workspace=self.workspace
        )
        self.endpoint_b = data_fixture.create_mcp_endpoint(
            user=self.user2, workspace=self.workspace
        )
        self.endpoint_c = data_fixture.create_mcp_endpoint(
            user=self.user1, workspace=self.workspace
        )
        for endpoint in (self.endpoint_a, self.endpoint_c):
            MCPProtectedField.objects.create(
                policy=endpoint.arabase_protection_policy, field=self.secret
            )
        self.view = ViewHandler().create_view(
            self.user1, self.table, HtmlPageViewType.type, name="Report", html=PAGE_V1
        )

    def fresh_view(self) -> HtmlPageView:
        return HtmlPageView.objects.get(id=self.view.id)

    def submit(self, endpoint, *, user=None, html=PAGE_V2, audience=None, ids=None):
        return submit_mcp_page_change(
            user=user or self.user1,
            endpoint=endpoint,
            view=self.fresh_view(),
            html=html,
            protected_field_ids=[self.secret.id] if ids is None else ids,
            audience=audience or ArtifactAudience.AUTHENTICATED,
        )

    def approve(self, endpoint, *, html=PAGE_V2, audience=None):
        pending = self.submit(endpoint, html=html, audience=audience)
        approve_artifact_draft(user=endpoint.user, draft_id=pending["draft_id"])
        return ArtifactApproval.objects.get(draft_id=pending["draft_id"])


@pytest.fixture
def setup(data_fixture):
    return Setup(data_fixture)


def feed_url(view):
    return reverse("api:database:views:html_page:list", kwargs={"view_id": view.id})


def public_feed_url(view):
    return reverse(
        "api:database:views:html_page:public_rows", kwargs={"slug": view.slug}
    )


# ---------------------------------------------------------------------------
# S1: a public-only publish by endpoint B over endpoint A's pending draft
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_public_only_publish_by_empty_endpoint_over_a_pending_protected_draft(
    api_client, setup
):
    s = setup
    pending = s.submit(s.endpoint_a)
    draft_id = pending["draft_id"]
    assert pending["status"] == "pending_approval"

    published = s.submit(s.endpoint_b, user=s.user2, html=PAGE_V3, ids=[])
    assert published["status"] == "published"
    state = HtmlPageArtifactState.objects.get(view=s.view)
    assert state.endpoint_id == s.endpoint_b.id
    # B's policy is empty, so the page has no protected output for B and the
    # state is not even marked public-only.
    assert state.public_only is False
    assert ArtifactDraft.objects.get(id=draft_id).status == ArtifactDraftStatus.PENDING

    view = s.fresh_view()
    assert view.html == PAGE_V3
    # Runtime access resolves state.endpoint (B) because there is no live
    # approval, so the page falls back to the unprotected legacy feed.
    assert page_runtime_access(view, user=s.user1).required is False
    assert page_feed_field_ids(view, user=s.user1) is None

    s.table.get_model().objects.create(
        **{f"field_{s.secret.id}": "canary", f"field_{s.visible.id}": "shown"}
    )
    api_client.force_authenticate(user=s.user1)
    feed = api_client.get(feed_url(view))
    assert feed.status_code == HTTP_200_OK
    assert set(feed.json()["results"][0]) == {
        "id",
        "order",
        f"field_{s.secret.id}",
        f"field_{s.visible.id}",
    }

    # The status read-model resolves the latest draft (A) instead.
    status = artifact_status_for_view(view)
    assert status["endpoint_id"] == s.endpoint_a.id
    assert status["artifact_state"] == "pending_approval"
    assert status["draft_id"] == draft_id

    # The REST draft endpoint answers 200 for B's public-only publish,
    # although the summary still carries A's pending draft id.
    api_client.force_authenticate(user=s.user2)
    response = api_client.post(
        reverse("api:arabase:mcp_artifact_draft"),
        {
            "endpoint_id": s.endpoint_b.id,
            "view_id": view.id,
            "html": PAGE_V3,
            "protected_field_ids": [],
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["status"] == "published"
    assert response.json()["draft_id"] == draft_id

    # A human source edit resolves the latest draft (A) and re-submits with
    # that draft's field ids and audience.
    api_client.force_authenticate(user=s.user1)
    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": view.id}),
        {"html": PAGE_V4},
        format="json",
    )
    assert response.status_code == HTTP_202_ACCEPTED
    body = response.json()
    assert body["status"] == "pending_approval"
    assert body["protected_field_ids"] == [s.secret.id]
    assert body["audience"] == ArtifactAudience.AUTHENTICATED
    new_draft = ArtifactDraft.objects.get(id=body["draft_id"])
    assert new_draft.id != draft_id
    assert new_draft.endpoint_id == s.endpoint_a.id
    assert new_draft.requested_field_ids == [s.secret.id]
    assert (
        ArtifactDraft.objects.get(id=draft_id).status == ArtifactDraftStatus.SUPERSEDED
    )
    assert s.fresh_view().html == PAGE_V3

    # Revocation resolves the latest draft's endpoint (A), owned by user1.
    with pytest.raises(PermissionDenied):
        revoke_artifact(user=s.user2, view_id=view.id)
    assert revoke_artifact(user=s.user1, view_id=view.id)["status"] == "revoked"


# ---------------------------------------------------------------------------
# S2: A holds an AUTHENTICATED approval and C a PUBLIC approval
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_live_approvals_per_audience_resolve_their_own_endpoint(api_client, setup):
    s = setup
    ViewHandler().update_view(s.user1, s.fresh_view(), public=True)
    approval_a = s.approve(s.endpoint_a, audience=ArtifactAudience.AUTHENTICATED)
    approval_c = s.approve(s.endpoint_c, audience=ArtifactAudience.PUBLIC)
    view = s.fresh_view()

    state = HtmlPageArtifactState.objects.get(view=view)
    assert state.active_approval_id == approval_c.id
    assert state.endpoint_id == s.endpoint_c.id

    authenticated = page_runtime_access(
        view, audience=ArtifactAudience.AUTHENTICATED, user=s.user1
    )
    assert authenticated.required is True
    assert authenticated.public_only is False
    assert authenticated.allowed_protected_field_ids == {s.secret.id}
    public = page_runtime_access(view, audience=ArtifactAudience.PUBLIC)
    assert public.required is True
    assert public.public_only is False
    assert public.allowed_protected_field_ids == {s.secret.id}

    expected_ids = {s.secret.id, s.visible.id}
    assert (
        page_feed_field_ids(view, audience=ArtifactAudience.AUTHENTICATED, user=s.user1)
        == expected_ids
    )
    assert page_feed_field_ids(view, audience=ArtifactAudience.PUBLIC) == expected_ids

    # The summary reports the newest live approval of any audience (C).
    status = artifact_status_for_view(view)
    assert status["endpoint_id"] == s.endpoint_c.id
    assert status["approval_id"] == approval_c.id
    assert status["artifact_state"] == "approved"
    assert status["audience"] == ArtifactAudience.PUBLIC
    assert _feed_query_endpoint(view) == s.endpoint_c
    assert approval_a.revoked_at is None

    ViewFilter.objects.create(
        view=view, field=s.secret, type="equal", value="sensitive"
    )
    view = s.fresh_view()

    with pytest.raises(ArtifactExposureBlocked):
        page_runtime_access(view, audience=ArtifactAudience.AUTHENTICATED, user=s.user1)
    with pytest.raises(ArtifactExposureBlocked):
        page_runtime_access(view, audience=ArtifactAudience.PUBLIC)

    api_client.force_authenticate(user=s.user1)
    response = api_client.get(feed_url(view))
    assert response.status_code == 423
    assert response.json()["code"] == "MCP_ARTIFACT_UNAVAILABLE"
    api_client.force_authenticate(user=None)
    response = api_client.get(public_feed_url(view))
    assert response.status_code == 423
    assert response.json()["code"] == "MCP_ARTIFACT_UNAVAILABLE"


# ---------------------------------------------------------------------------
# S3: fallbacks
# ---------------------------------------------------------------------------


def _orm_draft(endpoint, view, **extra):
    return ArtifactDraft.objects.create(
        endpoint=endpoint,
        view=view,
        candidate_html=PAGE_V3,
        content_digest="0" * 64,
        configuration_fingerprint="0" * 64,
        manifest_fingerprint="0" * 64,
        **extra,
    )


@pytest.mark.django_db
def test_revoke_falls_back_to_the_latest_draft_once_active_approval_is_cleared(
    setup,
):
    s = setup
    s.approve(s.endpoint_a)
    revoke_artifact(user=s.user1, view_id=s.view.id)
    state = HtmlPageArtifactState.objects.get(view=s.view)
    assert state.active_approval_id is None

    # The latest draft now belongs to B (user2): only user2 may revoke.
    _orm_draft(s.endpoint_b, s.fresh_view())
    with pytest.raises(PermissionDenied):
        revoke_artifact(user=s.user1, view_id=s.view.id)
    assert revoke_artifact(user=s.user2, view_id=s.view.id)["status"] == "revoked"
    assert (
        ArtifactAuditEvent.objects.filter(event_type="revoked")
        .order_by("-id")
        .first()
        .endpoint_id
        == s.endpoint_b.id
    )


@pytest.mark.django_db
def test_revoke_uses_active_approval_endpoint_even_when_revoked(setup):
    s = setup
    approval = s.approve(s.endpoint_a)
    ArtifactApproval.objects.filter(id=approval.id).update(revoked_at=timezone.now())
    state = HtmlPageArtifactState.objects.get(view=s.view)
    assert state.active_approval_id == approval.id
    _orm_draft(s.endpoint_b, s.fresh_view())

    with pytest.raises(PermissionDenied):
        revoke_artifact(user=s.user2, view_id=s.view.id)
    assert revoke_artifact(user=s.user1, view_id=s.view.id)["status"] == "revoked"
    # No live approval was left, so the pointer is kept and the audit carries
    # an empty audience.
    state.refresh_from_db()
    assert state.active_approval_id == approval.id
    event = ArtifactAuditEvent.objects.filter(event_type="revoked").get()
    assert event.audience == ""
    assert event.approval_id is None


@pytest.mark.django_db
def test_state_endpoint_becomes_none_when_its_endpoint_is_deleted(setup):
    s = setup
    s.submit(s.endpoint_b, user=s.user2, html=PAGE_V3, ids=[])
    state = HtmlPageArtifactState.objects.get(view=s.view)
    assert state.endpoint_id == s.endpoint_b.id

    s.endpoint_b.delete()
    state.refresh_from_db()
    assert state.endpoint_id is None

    view = s.fresh_view()
    with pytest.raises(ArtifactExposureBlocked):
        page_runtime_access(view, user=s.user1)
    with pytest.raises(ArtifactExposureBlocked):
        page_feed_field_ids(view, user=s.user1)
    status = artifact_status_for_view(view)
    assert status["endpoint_id"] is None
    assert status["artifact_state"] == "blocked"
    assert status["draft_id"] is None
    assert _feed_query_endpoint(view) is None


# ---------------------------------------------------------------------------
# S4: duplicated page whose source endpoint was deleted
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_duplicated_view_of_page_with_deleted_endpoint_fails_closed(api_client, setup):
    s = setup
    s.approve(s.endpoint_a)
    view_1 = s.fresh_view()
    view_2 = ViewHandler().create_view(
        s.user1, s.table, HtmlPageViewType.type, name="Copy", html=view_1.html
    )
    assert not HtmlPageArtifactState.objects.filter(view=view_2).exists()

    state = HtmlPageArtifactState.objects.get(view=view_1)
    s.endpoint_a.delete()
    state.refresh_from_db()
    assert state.endpoint_id is None

    view_2 = HtmlPageView.objects.get(id=view_2.id)
    with pytest.raises(ArtifactExposureBlocked):
        page_runtime_access(view_2, user=s.user1)

    api_client.force_authenticate(user=s.user1)
    response = api_client.get(feed_url(view_2))
    assert response.status_code == 423
    assert response.json() == {
        "code": "MCP_ARTIFACT_UNAVAILABLE",
        "message": (
            "This page is temporarily unavailable until its protected artifact "
            "is approved."
        ),
    }


# ---------------------------------------------------------------------------
# Feed-query dependency endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_feed_query_endpoint_prefers_live_approval_then_state_then_draft(setup):
    s = setup
    view = s.fresh_view()
    assert _feed_query_endpoint(view) is None

    draft_a = _orm_draft(s.endpoint_a, view)
    assert _feed_query_endpoint(view) == s.endpoint_a

    HtmlPageArtifactState.objects.create(view=view, endpoint=s.endpoint_b)
    assert _feed_query_endpoint(view) == s.endpoint_b

    draft_c = _orm_draft(s.endpoint_c, view)
    ArtifactApproval.objects.create(
        draft=draft_c,
        endpoint=s.endpoint_c,
        view=view,
        content_digest="0" * 64,
        configuration_fingerprint="0" * 64,
        manifest_fingerprint="0" * 64,
        policy_revision=1,
        access_generation=1,
        target_generation=1,
        audience=ArtifactAudience.AUTHENTICATED,
        audience_fingerprint="0" * 64,
        approved_at=timezone.now(),
    )
    assert _feed_query_endpoint(view) == s.endpoint_c
    assert draft_a.endpoint_id == s.endpoint_a.id


# ---------------------------------------------------------------------------
# View-setting edits never revoke an approval
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_view_setting_edits_never_revoke_an_approval(setup):
    s = setup
    approval = s.approve(s.endpoint_a)
    page_runtime_access(s.fresh_view(), user=s.user1)

    def assert_not_revoked_but_blocked():
        approval.refresh_from_db()
        assert approval.revoked_at is None
        assert not ArtifactAuditEvent.objects.filter(event_type="invalidated").exists()
        with pytest.raises(ArtifactExposureBlocked):
            page_runtime_access(s.fresh_view(), user=s.user1)

    ViewHandler().create_filter(s.user1, s.fresh_view(), s.visible, "equal", "x")
    assert_not_revoked_but_blocked()

    ViewHandler().update_view(s.user1, s.fresh_view(), name="Renamed")
    assert s.fresh_view().name == "Renamed"
    assert_not_revoked_but_blocked()


def test_no_view_signal_invalidation_path_remains():
    from arabase.mcp.protection import artifact_commands

    for name in (
        "invalidate_artifact_for_view",
        "connect_artifact_lifecycle",
        "_internal_artifact_update",
        "view_signals",
    ):
        assert not hasattr(artifact_commands, name)
