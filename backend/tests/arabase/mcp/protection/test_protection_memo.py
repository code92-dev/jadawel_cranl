"""The request-scoped memo of the artifact layer.

Inside ``request_scope()`` an endpoint's policy and the protected output of each
(endpoint, table) pair are computed once.  Only successful results are stored,
an endpoint of ``None`` always bypasses the memo, and masking never uses it.

The query-count pins were recorded before the memo existed: an approved
protected page-feed GET issued 60 queries and ``artifact_status_for_view`` 26.
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest

from arabase.mcp.page import services
from arabase.mcp.protection import artifact_boundary
from arabase.mcp.protection.artifact_boundary import (
    ArtifactExposureBlocked,
    artifact_status_for_view,
    page_runtime_access,
    protected_output_for_view,
    request_scope,
)
from arabase.mcp.protection.artifact_commands import approve_artifact_draft
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactDraft,
    MCPProtectedField,
)
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.core.mcp.errors import MCPErrorCode, SafeMCPToolError

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"


class Page:
    """An approved protected page: Secret is protected, Visible is not."""

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

    def approve(self):
        pending = services.update_page_view(
            self.user,
            self.workspace,
            self.view.id,
            html=PAGE_V2,
            endpoint=self.endpoint,
            protected_field_ids=[self.secret.id],
        )
        approve_artifact_draft(user=self.user, draft_id=pending["draft_id"])
        model = self.table.get_model(attribute_names=True)
        self.rows = [
            model.objects.create(secret="s1", visible="v1"),
            model.objects.create(secret="s2", visible="v2"),
        ]

    def fresh_view(self) -> HtmlPageView:
        return HtmlPageView.objects.get(id=self.view.id)


@pytest.fixture
def page(data_fixture):
    return Page(data_fixture)


def _count_queries(callable_):
    with CaptureQueriesContext(connection) as ctx:
        result = callable_()
    return len(ctx.captured_queries), result


@pytest.mark.django_db
def test_protected_output_is_memoized_only_inside_a_scope(page):
    view = page.fresh_view()

    first, output = _count_queries(
        lambda: protected_output_for_view(view, page.endpoint)
    )
    second, again = _count_queries(
        lambda: protected_output_for_view(view, page.endpoint)
    )
    assert first > 0
    assert second == first
    assert [item.field_id for item in output] == [page.secret.id]
    assert [item.field_id for item in again] == [page.secret.id]

    with request_scope():
        inside_first, cached = _count_queries(
            lambda: protected_output_for_view(view, page.endpoint)
        )
        inside_second, cached_again = _count_queries(
            lambda: protected_output_for_view(view, page.endpoint)
        )
        policy_queries, _policy = _count_queries(
            lambda: artifact_boundary._policy_for_endpoint(page.endpoint)
        )
    assert inside_first == first
    assert inside_second == 0
    assert cached_again is cached
    assert policy_queries == 0
    assert [item.field_id for item in cached] == [page.secret.id]


@pytest.mark.django_db
def test_failed_policy_loads_are_never_cached(page, monkeypatch):
    view = page.fresh_view()
    real_load = artifact_boundary.get_mcp_protection_policy_state
    calls = []

    def fail_once(endpoint):
        calls.append(endpoint.id)
        if len(calls) == 1:
            raise RuntimeError("transient policy failure")
        return real_load(endpoint)

    monkeypatch.setattr(artifact_boundary, "get_mcp_protection_policy_state", fail_once)

    with request_scope():
        with pytest.raises(ArtifactExposureBlocked):
            protected_output_for_view(view, page.endpoint)
        output = protected_output_for_view(view, page.endpoint)
        protected_output_for_view(view, page.endpoint)

    assert calls == [page.endpoint.id, page.endpoint.id]
    assert [item.field_id for item in output] == [page.secret.id]


@pytest.mark.django_db
def test_graph_errors_escape_unwrapped_and_are_never_cached(page, monkeypatch):
    view = page.fresh_view()
    real_fields = artifact_boundary.protected_output_fields
    calls = []

    def fail_once(*args):
        calls.append(args[0])
        if len(calls) == 1:
            raise SafeMCPToolError(MCPErrorCode.PROTECTION_UNAVAILABLE, retryable=False)
        return real_fields(*args)

    monkeypatch.setattr(artifact_boundary, "protected_output_fields", fail_once)

    with request_scope():
        with pytest.raises(SafeMCPToolError):
            protected_output_for_view(view, page.endpoint)
        output = protected_output_for_view(view, page.endpoint)
        protected_output_for_view(view, page.endpoint)

    assert calls == [page.table.id, page.table.id]
    assert [item.field_id for item in output] == [page.secret.id]


@pytest.mark.django_db
def test_nested_scopes_share_one_cache_that_is_dropped_on_exit(page):
    view = page.fresh_view()
    assert artifact_boundary._request_cache.get() is None

    with request_scope():
        outer_cache = artifact_boundary._request_cache.get()
        first, _ = _count_queries(
            lambda: protected_output_for_view(view, page.endpoint)
        )
        with request_scope():
            assert artifact_boundary._request_cache.get() is outer_cache
            nested, _ = _count_queries(
                lambda: protected_output_for_view(view, page.endpoint)
            )
        assert artifact_boundary._request_cache.get() is outer_cache
        after_nested, _ = _count_queries(
            lambda: protected_output_for_view(view, page.endpoint)
        )

    assert first > 0
    assert nested == 0
    assert after_nested == 0
    assert artifact_boundary._request_cache.get() is None
    fresh, _ = _count_queries(lambda: protected_output_for_view(view, page.endpoint))
    assert fresh == first


@pytest.mark.django_db
def test_decorated_entry_points_leave_no_cache_behind(page):
    page.approve()

    assert page_runtime_access(page.fresh_view(), user=page.user).required
    assert artifact_boundary._request_cache.get() is None
    artifact_status_for_view(page.fresh_view())
    assert artifact_boundary._request_cache.get() is None


@pytest.mark.django_db
def test_a_missing_endpoint_bypasses_the_memo_and_fails_closed(page):
    view = page.fresh_view()

    with request_scope():
        for _ in range(2):
            with pytest.raises(ArtifactExposureBlocked) as blocked:
                protected_output_for_view(view, None)
            assert not isinstance(blocked.value, AttributeError)
        assert artifact_boundary._request_cache.get() == {}

    with pytest.raises(ArtifactExposureBlocked):
        protected_output_for_view(view, None)


@pytest.mark.django_db
def test_approved_page_feed_issues_fewer_queries_with_the_same_body(
    api_client, page, django_assert_num_fork_queries
):
    page.approve()
    api_client.force_authenticate(user=page.user)
    url = reverse("api:database:views:html_page:list", kwargs={"view_id": page.view.id})
    api_client.get(url)

    # Recorded before the memo: 60 queries. The memo brings it to 36, and the
    # hidden-field hook reusing the permission check's cached workspace role
    # (arabase.permissions.table_grants.workspace_roles) saves one more.
    with django_assert_num_fork_queries(35):
        response = api_client.get(url)

    assert response.status_code == 200
    assert response.json() == {
        "count": 2,
        "row_limit": 200,
        "truncated": False,
        "results": [
            {
                "id": row.id,
                "order": "1.00000000000000000000",
                f"field_{page.secret.id}": secret,
                f"field_{page.visible.id}": visible,
            }
            for row, secret, visible in zip(page.rows, ("s1", "s2"), ("v1", "v2"))
        ],
    }


@pytest.mark.django_db
def test_artifact_status_issues_fewer_queries_with_the_same_summary(
    page, django_assert_num_queries
):
    page.approve()
    approval = ArtifactApproval.objects.get(view_id=page.view.id)
    draft = ArtifactDraft.objects.get(id=approval.draft_id)
    view = page.fresh_view()
    artifact_status_for_view(view)
    view = page.fresh_view()

    # Recorded before the memo: 26 queries.
    with django_assert_num_queries(24):
        status = artifact_status_for_view(view)

    assert status == {
        "view_id": page.view.id,
        "artifact_state": "approved",
        "target_generation": approval.target_generation,
        "approval_id": approval.id,
        "draft_id": draft.id,
        "audience": "authenticated",
        "endpoint_id": page.endpoint.id,
        "protected_field_ids": [page.secret.id],
        "manifest": [{"field_id": page.secret.id, "provenance": "direct"}],
        "view_configuration": {
            "table_id": page.table.id,
            "row_limit": 200,
            "public": False,
            "allow_external_resources": False,
            "filter_type": "AND",
            "filter_count": 0,
            "sort_count": 0,
            "group_count": 0,
        },
    }
