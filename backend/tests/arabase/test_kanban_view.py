"""Tests for the OSS kanban view type (#35).

The kanban view is a board grouped by a single select field. The board
endpoint returns one stack per option (plus the stack of rows without a
value) with row counts, the stack endpoint returns one page of rows per
stack, and the view supports decorations so row colors work on its cards.
"""

from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from jadawel.contrib.database.rows.handler import RowHandler
from jadawel.contrib.database.views.actions import UpdateViewActionType
from jadawel.contrib.database.views.registries import view_type_registry
from jadawel.core.action.handler import ActionHandler


@pytest.fixture
def kanban_setup(data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    status = data_fixture.create_single_select_field(table=table, name="Status")
    option_open = data_fixture.create_select_option(
        field=status, value="Open", color="blue"
    )
    option_doing = data_fixture.create_select_option(
        field=status, value="Doing", color="green"
    )
    option_closed = data_fixture.create_select_option(
        field=status, value="Closed", color="gray"
    )
    text = data_fixture.create_text_field(table=table, name="Notes")

    row_handler = RowHandler()
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{status.id}": option_open.id, f"field_{text.id}": "one"},
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{status.id}": option_open.id, f"field_{text.id}": "two"},
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{status.id}": option_doing.id},
    )
    row_handler.create_row(user=user, table=table, values={})

    return {
        "user": user,
        "token": token,
        "table": table,
        "status": status,
        "option_open": option_open,
        "option_doing": option_doing,
        "option_closed": option_closed,
        "text": text,
    }


def auth(token):
    return {"HTTP_AUTHORIZATION": f"JWT {token}"}


def create_kanban_view(api_client, setup, **extra):
    return api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": setup["table"].id}),
        {"name": "Board", "type": "kanban", **extra},
        format="json",
        **auth(setup["token"]),
    )


def kanban_url(view_id):
    return reverse(
        "api:database:views:kanban:view",
        kwargs={"view_id": view_id},
    )


def stack_url(view_id, select_option_id):
    return reverse(
        "api:database:views:kanban:stack_rows",
        kwargs={"view_id": view_id, "select_option_id": str(select_option_id)},
    )


@pytest.mark.django_db
def test_kanban_view_type_is_registered():
    view_type = view_type_registry.get("kanban")
    assert view_type.can_decorate is True
    assert view_type.model_class.__name__ == "KanbanView"


@pytest.mark.django_db
def test_kanban_board_lists_stacks_with_counts(api_client, kanban_setup):
    setup = kanban_setup
    created = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    )
    assert created.status_code == HTTP_200_OK, created.content
    view_id = created.json()["id"]

    response = api_client.get(kanban_url(view_id), **auth(setup["token"]))
    assert response.status_code == HTTP_200_OK, response.content
    stacks = response.json()["stacks"]

    assert [(stack["title"], stack["color"], stack["count"]) for stack in stacks] == [
        ("Open", "blue", 2),
        ("Doing", "green", 1),
        ("Closed", "gray", 0),
        (None, None, 1),
    ]
    assert stacks[-1]["id"] is None


@pytest.mark.django_db
def test_kanban_board_without_grouping_field_is_empty(api_client, kanban_setup):
    setup = kanban_setup
    created = create_kanban_view(api_client, setup)
    assert created.status_code == HTTP_200_OK, created.content

    response = api_client.get(kanban_url(created.json()["id"]), **auth(setup["token"]))
    assert response.status_code == HTTP_200_OK
    assert response.json()["stacks"] == []


@pytest.mark.django_db
def test_kanban_stack_rows(api_client, kanban_setup):
    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]

    open_stack = api_client.get(
        stack_url(view_id, setup["option_open"].id), **auth(setup["token"])
    )
    assert open_stack.status_code == HTTP_200_OK, open_stack.content
    body = open_stack.json()
    assert body["count"] == 2
    notes = {row[f"field_{setup['text'].id}"] for row in body["results"]}
    assert notes == {"one", "two"}

    empty_stack = api_client.get(
        stack_url(view_id, setup["option_closed"].id), **auth(setup["token"])
    )
    assert empty_stack.status_code == HTTP_200_OK
    assert empty_stack.json()["count"] == 0

    null_stack = api_client.get(stack_url(view_id, "null"), **auth(setup["token"]))
    assert null_stack.status_code == HTTP_200_OK, null_stack.content
    assert null_stack.json()["count"] == 1


@pytest.mark.django_db
def test_kanban_stack_rows_errors(api_client, kanban_setup):
    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]

    unknown = api_client.get(stack_url(view_id, 999999), **auth(setup["token"]))
    assert unknown.status_code == HTTP_404_NOT_FOUND
    assert unknown.json()["error"] == "ERROR_KANBAN_VIEW_STACK_DOES_NOT_EXIST"

    no_field_view = create_kanban_view(api_client, setup).json()["id"]
    no_field = api_client.get(
        stack_url(no_field_view, setup["option_open"].id), **auth(setup["token"])
    )
    assert no_field.status_code == HTTP_400_BAD_REQUEST
    assert no_field.json()["error"] == "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD"


@pytest.mark.django_db
def test_kanban_view_validates_field_references(api_client, kanban_setup):
    setup = kanban_setup
    wrong_type = create_kanban_view(
        api_client, setup, single_select_field=setup["text"].id
    )
    assert wrong_type.status_code == HTTP_400_BAD_REQUEST
    assert wrong_type.json()["error"] == "ERROR_INCOMPATIBLE_FIELD"


@pytest.mark.django_db
def test_kanban_view_rejects_foreign_table_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    other_table = data_fixture.create_database_table(user=user)
    foreign_field = data_fixture.create_single_select_field(table=other_table)

    response = api_client.post(
        reverse("api:database:views:list", kwargs={"table_id": table.id}),
        {"name": "Board", "type": "kanban", "single_select_field": foreign_field.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_FIELD_NOT_IN_TABLE"


@pytest.mark.django_db
def test_kanban_field_delete_clears_grouping_reference(
    api_client, data_fixture, kanban_setup
):
    from jadawel.contrib.database.fields.handler import FieldHandler

    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]

    FieldHandler().delete_field(setup["user"], setup["status"])

    response = api_client.get(kanban_url(view_id), **auth(setup["token"]))
    assert response.status_code == HTTP_200_OK
    assert response.json()["stacks"] == []


@pytest.mark.django_db
def test_kanban_grouping_field_can_be_set_via_view_endpoint(api_client, kanban_setup):
    """Setting the grouping field after creation must not 500.

    The core view endpoint records an ``update_view`` undo/redo action whose
    params come from ``export_prepared_values``; exporting the field
    reference as a model instance instead of an id crashed the action's JSON
    serialization (user-reported: selecting the kanban grouping field from
    the toolbar returned 500 and the board never grouped).
    """

    setup = kanban_setup
    view_id = create_kanban_view(api_client, setup).json()["id"]

    response = api_client.patch(
        reverse("api:database:views:item", kwargs={"view_id": view_id}),
        {"single_select_field": setup["status"].id},
        format="json",
        HTTP_CLIENTSESSIONID="test-session",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_200_OK, response.content
    assert response.json()["single_select_field"] == setup["status"].id

    board = api_client.get(kanban_url(view_id), **auth(setup["token"]))
    assert board.status_code == HTTP_200_OK, board.content
    assert [stack["count"] for stack in board.json()["stacks"]] == [2, 1, 0, 1]

    # Undo must round-trip the exported ids back through prepare_values.
    ActionHandler.undo(
        setup["user"], [UpdateViewActionType.scope(view_id)], "test-session"
    )
    board = api_client.get(kanban_url(view_id), **auth(setup["token"]))
    # Ungrouped again: the board reports its not-configured empty shape.
    assert board.json()["stacks"] == []


@pytest.mark.django_db
def test_kanban_view_supports_decorations(api_client, data_fixture, kanban_setup):
    """#35 is the colors story: decorations must be creatable on a kanban view."""

    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]

    response = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_id}),
        {
            "type": "background_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {"field_id": setup["status"].id},
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_200_OK, response.content
    assert response.json()["type"] == "background_color"


@pytest.mark.django_db
def test_kanban_view_is_read_only_for_viewers(api_client, data_fixture, kanban_setup):
    """The VIEWER role (#36) applies to the kanban board like any other view."""

    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]

    viewer, viewer_token = data_fixture.create_user_and_token()
    data_fixture.create_user_workspace(
        workspace=setup["table"].database.workspace,
        user=viewer,
        permissions="VIEWER",
    )

    board = api_client.get(kanban_url(view_id), **auth(viewer_token))
    assert board.status_code == HTTP_200_OK, board.content
    assert len(board.json()["stacks"]) == 4

    denied = api_client.post(
        reverse("api:database:views:list_decorations", kwargs={"view_id": view_id}),
        {
            "type": "background_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {"field_id": setup["status"].id},
        },
        format="json",
        **auth(viewer_token),
    )
    assert denied.status_code == HTTP_401_UNAUTHORIZED
    assert denied.json()["error"] == "PERMISSION_DENIED"
