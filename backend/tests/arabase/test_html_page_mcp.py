"""The MCP tools that author a page.

An MCP endpoint hands a model the authority of the user behind it, scoped to one
workspace. So the assertions worth making are about those two limits holding —
somebody outside the workspace cannot rewrite a page, and an endpoint cannot
reach across into another of the same user's workspaces — plus the revision
history that makes an AI's overwrite recoverable.
"""

import pytest

from arabase.mcp.page import services
from arabase.views.constants import MAX_ROW_LIMIT
from arabase.views.exceptions import (
    HtmlPageViewDoesNotExist,
    HtmlPageViewRevisionDoesNotExist,
)
from arabase.views.handler import HtmlPageRevisionHandler
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.core.exceptions import PermissionException

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
PAGE_V2 = "<!doctype html><body><h1>v2</h1></body>"


@pytest.fixture
def workspace_table(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name")
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    return user, workspace, table, endpoint


@pytest.mark.django_db
def test_create_then_read_a_page(workspace_table):
    user, workspace, table, endpoint = workspace_table

    created = services.create_page_view(
        user, workspace, table.id, "Report", PAGE_V1, endpoint=endpoint
    )

    assert created["name"] == "Report"
    assert created["html_bytes"] == len(PAGE_V1)
    assert created["is_public"] is False

    read = services.get_page_view(
        user, workspace, created["view_id"], endpoint=endpoint
    )

    assert read["html"] == PAGE_V1
    assert [field["name"] for field in read["fields"]] == ["Name"]
    # The contract is returned as data rather than sitting in a tool docstring,
    # where MCP would collapse its whitespace into one unreadable line. What the
    # model most needs from it is that the page has no network.
    assert "connect-src 'none'" in read["runtime_contract"]
    assert "\n" in read["runtime_contract"]


@pytest.mark.django_db
def test_the_sample_shows_the_real_row_shape(workspace_table, data_fixture):
    user, workspace, table, endpoint = workspace_table
    model = table.get_model()
    for index in range(8):
        model.objects.create(order=index)

    read = services.get_page_view(
        user, workspace, _new_page(user, workspace, table), endpoint=endpoint
    )

    assert read["row_count"] == 8
    assert len(read["row_sample"]) == services.SAMPLE_ROW_COUNT


@pytest.mark.django_db
def test_listing_only_returns_page_views(workspace_table, data_fixture):
    user, workspace, table, _ = workspace_table
    data_fixture.create_grid_view(table=table)
    _new_page(user, workspace, table)

    listed = services.list_page_views(user, workspace, table.id)

    assert len(listed) == 1
    assert listed[0]["name"] == "Report"


@pytest.mark.django_db
def test_updating_keeps_the_previous_version(workspace_table):
    user, workspace, table, endpoint = workspace_table
    view_id = _new_page(user, workspace, table)

    services.update_page_view(user, workspace, view_id, html=PAGE_V2, endpoint=endpoint)

    revisions = services.list_page_revisions(user, workspace, view_id)
    assert len(revisions) == 1
    assert revisions[0]["html_bytes"] == len(PAGE_V1)

    services.restore_page_revision(
        user, workspace, view_id, revisions[0]["revision_id"], endpoint=endpoint
    )

    assert (
        services.get_page_view(
            user, workspace, view_id, include_rows=False, endpoint=endpoint
        )["html"]
        == PAGE_V1
    )


@pytest.mark.django_db
def test_a_rename_does_not_burn_a_revision(workspace_table):
    user, workspace, table, endpoint = workspace_table
    view_id = _new_page(user, workspace, table)

    services.update_page_view(
        user, workspace, view_id, name="Renamed", endpoint=endpoint
    )

    assert services.list_page_revisions(user, workspace, view_id) == []


@pytest.mark.django_db
def test_the_history_is_bounded(workspace_table):
    user, workspace, table, _ = workspace_table
    view_id = _new_page(user, workspace, table)
    view = HtmlPageView.objects.get(id=view_id)
    handler = HtmlPageRevisionHandler()

    from arabase.views.constants import MAX_REVISIONS

    for index in range(MAX_REVISIONS + 5):
        view.html = f"<p>{index}</p>"
        view.save()
        handler.snapshot(view, user)

    assert view.revisions.count() == MAX_REVISIONS


@pytest.mark.django_db
def test_restoring_an_unrelated_revision_is_refused(workspace_table):
    user, workspace, table, endpoint = workspace_table
    first = _new_page(user, workspace, table)
    second = _new_page(user, workspace, table, name="Other")

    services.update_page_view(user, workspace, first, html=PAGE_V2, endpoint=endpoint)
    revision_id = services.list_page_revisions(user, workspace, first)[0]["revision_id"]

    with pytest.raises(HtmlPageViewRevisionDoesNotExist):
        services.restore_page_revision(
            user, workspace, second, revision_id, endpoint=endpoint
        )


@pytest.mark.django_db
def test_row_limit_is_clamped_through_the_tool(workspace_table):
    user, workspace, table, endpoint = workspace_table
    view_id = _new_page(user, workspace, table)

    result = services.update_page_view(
        user, workspace, view_id, row_limit=1_000_000, endpoint=endpoint
    )

    assert result["row_limit"] == MAX_ROW_LIMIT


@pytest.mark.django_db
def test_an_endpoint_cannot_reach_another_workspace(workspace_table, data_fixture):
    user, workspace, table, endpoint = workspace_table
    view_id = _new_page(user, workspace, table)

    # The same user, a second workspace: the endpoint is bound to one of them,
    # and reading the view is not enough to make it in scope for the other.
    other_workspace = data_fixture.create_workspace(user=user)

    with pytest.raises(HtmlPageViewDoesNotExist):
        services.get_page_view(user, other_workspace, view_id, endpoint=endpoint)

    with pytest.raises(HtmlPageViewDoesNotExist):
        services.update_page_view(
            user, other_workspace, view_id, html=PAGE_V2, endpoint=endpoint
        )


@pytest.mark.django_db
def test_someone_outside_the_workspace_cannot_rewrite_a_page(
    workspace_table, data_fixture
):
    user, workspace, table, endpoint = workspace_table
    view_id = _new_page(user, workspace, table)

    outsider = data_fixture.create_user()

    # Reported as "does not exist" rather than "forbidden", on purpose: see
    # `_get_page_view`. Either way the write must not land.
    with pytest.raises((PermissionException, HtmlPageViewDoesNotExist)):
        services.update_page_view(
            outsider, workspace, view_id, html=PAGE_V2, endpoint=endpoint
        )

    assert HtmlPageView.objects.get(id=view_id).html == PAGE_V1


@pytest.mark.django_db
def test_tools_are_registered():
    from jadawel.core.mcp.registries import mcp_tool_registry

    for name in [
        "list_page_views",
        "get_page_view",
        "create_page_view",
        "update_page_view",
        "list_page_view_revisions",
        "restore_page_view_revision",
    ]:
        assert mcp_tool_registry.get(name) is not None


def _new_page(user, workspace, table, name="Report"):
    """Create a page through the handler and return its id."""

    view = ViewHandler().create_view(
        user, table, HtmlPageViewType.type, name=name, html=PAGE_V1
    )
    return view.id
