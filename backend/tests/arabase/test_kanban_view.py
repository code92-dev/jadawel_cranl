"""Tests for the OSS kanban view type (#35).

The kanban view is a board grouped by a single select field. The board
endpoint returns one stack per option (plus the stack of rows without a
value) with row counts, the stack endpoint returns one page of rows per
stack, and the view supports decorations so row colors work on its cards.
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from arabase.kanban.models import KanbanView, KanbanViewFieldOptions
from jadawel.contrib.database.fields.handler import FieldHandler
from jadawel.contrib.database.fields.models import SelectOption
from jadawel.contrib.database.rows.handler import RowHandler
from jadawel.contrib.database.views.actions import UpdateViewActionType
from jadawel.contrib.database.views.handler import ViewHandler
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


@pytest.fixture
def filtered_board(api_client, data_fixture):
    """A board whose rows are narrowed by a stored filter and a search.

    Every stack holds rows that the `contains_not "skip"` view filter or the
    `?search=alpha` query drops, so each count shows that both apply. Two
    options are deleted after rows use them:

    * "Dropped" goes through the field handler, which sets its rows to
      NULL first, so its row joins the stack of rows without a value.
    * "Stale" is raw-deleted, so its row keeps an id that matches no option
      and belongs to no stack, not even the NULL one.
    """

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field_handler = FieldHandler()
    status = field_handler.create_field(
        user=user,
        table=table,
        type_name="single_select",
        name="Status",
        select_options=[
            {"value": "Open", "color": "blue"},
            {"value": "Doing", "color": "green"},
            {"value": "Closed", "color": "gray"},
            {"value": "Dropped", "color": "red"},
            {"value": "Stale", "color": "dark-red"},
        ],
    )
    options = {option.value: option for option in status.select_options.all()}
    notes = data_fixture.create_text_field(table=table, name="Notes")

    row_handler = RowHandler()
    for option_name, text in [
        ("Open", "alpha one"),
        ("Open", "alpha two"),
        ("Open", "beta"),
        ("Doing", "alpha three"),
        ("Doing", "alpha skip"),
        ("Closed", "beta closed"),
        (None, "alpha four"),
        (None, "beta none"),
        (None, "alpha skip none"),
        ("Dropped", "alpha dropped"),
        ("Dropped", "beta dropped"),
        ("Stale", "alpha stale"),
    ]:
        option = options[option_name].id if option_name else None
        row_handler.create_row(
            user=user,
            table=table,
            values={f"field_{status.id}": option, f"field_{notes.id}": text},
        )

    created = create_kanban_view(
        api_client,
        {"table": table, "token": token},
        single_select_field=status.id,
    )
    assert created.status_code == HTTP_200_OK, created.content
    view = KanbanView.objects.get(id=created.json()["id"])
    data_fixture.create_view_filter(
        view=view, field=notes, type="contains_not", value="skip"
    )

    kept = [options[name] for name in ("Open", "Doing", "Closed", "Stale")]
    field_handler.update_field(
        user=user,
        field=status,
        select_options=[
            {"id": option.id, "value": option.value, "color": option.color}
            for option in kept
        ],
    )
    SelectOption.objects.filter(id=options["Stale"].id)._raw_delete(
        SelectOption.objects.db
    )

    return {
        "token": token,
        "table": table,
        "view": view,
        "options": options,
    }


@pytest.mark.django_db
def test_kanban_board_stacks_under_a_filter_and_a_search(api_client, filtered_board):
    board = filtered_board
    options = board["options"]
    url = f"{kanban_url(board['view'].id)}?search=alpha"

    response = api_client.get(url, **auth(board["token"]))
    assert response.status_code == HTTP_200_OK, response.content
    assert response.json()["stacks"] == [
        {
            "id": options["Open"].id,
            "title": "Open",
            "color": "blue",
            "count": 2,
        },
        {
            "id": options["Doing"].id,
            "title": "Doing",
            "color": "green",
            "count": 1,
        },
        {
            "id": options["Closed"].id,
            "title": "Closed",
            "color": "gray",
            "count": 0,
        },
        {"id": None, "title": None, "color": None, "count": 2},
    ]

    null_stack = api_client.get(
        f"{stack_url(board['view'].id, 'null')}?search=alpha", **auth(board["token"])
    )
    assert null_stack.status_code == HTTP_200_OK, null_stack.content
    assert null_stack.json()["count"] == 2

    without_search = api_client.get(
        kanban_url(board["view"].id), **auth(board["token"])
    )
    assert [stack["count"] for stack in without_search.json()["stacks"]] == [
        3,
        1,
        1,
        4,
    ]


@pytest.mark.django_db
def test_kanban_board_row_queries(api_client, filtered_board):
    """The board reads the user table twice: grouped counts, then the NULL count.

    The second query is not redundant: see
    `test_kanban_board_null_stack_counts_each_row_once`.
    """

    board = filtered_board
    url = f"{kanban_url(board['view'].id)}?search=alpha"
    user_table = f'"database_table_{board["table"].id}"'
    # The first request warms the per-process caches.
    api_client.get(url, **auth(board["token"]))

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(url, **auth(board["token"]))

    assert response.status_code == HTTP_200_OK, response.content
    row_queries = [q["sql"] for q in queries if user_table in q["sql"]]
    assert len(row_queries) == 2
    assert "GROUP BY" in row_queries[0]
    assert "IS NULL" in row_queries[1]
    assert row_queries[1].startswith("SELECT COUNT(*)")
    # The optional plugins (JADAWEL_PLUGIN_DIR) add their own permission
    # lookups to every request; the budget covers the application's queries.
    plugin_tables = ('"jadawel_organizations_', '"jadawel_billing_')
    fork_queries = [
        q["sql"] for q in queries if not any(t in q["sql"] for t in plugin_tables)
    ]
    assert len(fork_queries) <= 16


@pytest.mark.django_db
def test_kanban_board_null_stack_counts_each_row_once(api_client, data_fixture):
    """The NULL stack keeps its own COUNT over distinct rows.

    A filter or search that reaches a link row or multiple select field can
    repeat a row once per match, or group it through an aggregate. The
    per-option counts come from one grouped query that counts those repeats:
    "Open" holds one row but shows 2 here, and that is pinned as it is. The
    NULL count has always come from a separate COUNT over distinct rows. The
    grouped query's own NULL bucket would say 2 in the first case below and 1
    in the second, so it cannot replace that COUNT.
    """

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field_handler = FieldHandler()
    status = field_handler.create_field(
        user=user,
        table=table,
        type_name="single_select",
        name="Status",
        select_options=[
            {"value": "Open", "color": "blue"},
            {"value": "Doing", "color": "green"},
        ],
    )
    open_option, doing_option = status.select_options.all()
    tags = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_select",
        name="Tags",
        select_options=[
            {"value": "alpha x", "color": "blue"},
            {"value": "alpha y", "color": "red"},
        ],
    )
    both_tags = [option.id for option in tags.select_options.all()]
    notes = data_fixture.create_text_field(table=table, name="Notes")
    linked_table = data_fixture.create_database_table(
        user=user, database=table.database
    )
    linked_primary = data_fixture.create_text_field(
        table=linked_table, primary=True, name="Name"
    )
    link = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Link",
        link_row_table=linked_table,
    )

    row_handler = RowHandler()
    first, second = [
        row_handler.create_row(
            user=user,
            table=linked_table,
            values={f"field_{linked_primary.id}": name},
        )
        for name in ("alpha one", "alpha two")
    ]
    for option, row_tags, links, text in [
        (None, both_tags, [first.id, second.id], "zzz"),
        (None, [], [], "alpha"),
        (open_option.id, both_tags, [first.id, second.id], "zzz"),
        (doing_option.id, [], [first.id], "alpha"),
    ]:
        row_handler.create_row(
            user=user,
            table=table,
            values={
                f"field_{status.id}": option,
                f"field_{tags.id}": row_tags,
                f"field_{link.id}": links,
                f"field_{notes.id}": text,
            },
        )

    created = create_kanban_view(
        api_client,
        {"table": table, "token": token},
        single_select_field=status.id,
    )
    assert created.status_code == HTTP_200_OK, created.content
    view = KanbanView.objects.get(id=created.json()["id"])

    def counts(query=""):
        response = api_client.get(f"{kanban_url(view.id)}{query}", **auth(token))
        assert response.status_code == HTTP_200_OK, response.content
        return [stack["count"] for stack in response.json()["stacks"]]

    has_first = data_fixture.create_view_filter(
        view=view, field=link, type="link_row_has", value=str(first.id)
    )
    assert counts("?search=alpha") == [2, 1, 1]

    has_first.delete()
    view.filter_type = "OR"
    view.save(update_fields=["filter_type"])
    for field in (link, notes, tags):
        data_fixture.create_view_filter(
            view=view,
            field=field,
            type="link_row_contains" if field is link else "contains",
            value="alpha",
        )
    assert counts() == [2, 1, 2]


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
def test_kanban_endpoints_check_the_view_first(api_client, data_fixture, kanban_setup):
    """Both endpoints look the view up and check access before anything else."""

    setup = kanban_setup
    view_id = create_kanban_view(
        api_client, setup, single_select_field=setup["status"].id
    ).json()["id"]
    no_field_view_id = create_kanban_view(api_client, setup).json()["id"]
    _, outsider_token = data_fixture.create_user_and_token()

    for url in (
        kanban_url(view_id),
        stack_url(view_id, 999999),
        stack_url(no_field_view_id, setup["option_open"].id),
    ):
        response = api_client.get(url, **auth(outsider_token))
        assert response.status_code == HTTP_400_BAD_REQUEST, url
        assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    for url in (kanban_url(999999), stack_url(999999, "null")):
        response = api_client.get(url, **auth(setup["token"]))
        assert response.status_code == HTTP_404_NOT_FOUND, url
        assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


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


@pytest.mark.django_db
def test_kanban_hidden_fields(data_fixture, django_assert_num_queries):
    """A field without an option, or with a hidden one, is hidden.

    The stacking and cover fields are never hidden, and a call that only
    checks those two sends no field-options query at all.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    primary = data_fixture.create_text_field(table=table, primary=True, name="Name")
    status = data_fixture.create_single_select_field(table=table, name="Status")
    cover = data_fixture.create_file_field(table=table, name="Cover")
    shown = data_fixture.create_text_field(table=table, name="Shown")
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    view = ViewHandler().create_view(
        user,
        table,
        "kanban",
        name="Board",
        single_select_field=status.id,
        card_cover_image_field=cover.id,
    )
    view.get_field_options(create_if_missing=True)
    KanbanViewFieldOptions.objects.filter(kanban_view=view).update(hidden=True)
    KanbanViewFieldOptions.objects.filter(
        kanban_view=view, field_id__in=[primary.id, shown.id]
    ).update(hidden=False)
    added_later = data_fixture.create_text_field(table=table, name="Added later")
    KanbanViewFieldOptions.objects.filter(field=added_later).delete()

    view_type = view_type_registry.get("kanban")

    def fresh_view():
        return KanbanView.objects.get(id=view.id)

    assert view_type.get_hidden_fields(fresh_view()) == {hidden.id, added_later.id}
    assert view_type.get_hidden_fields(
        fresh_view(), field_ids_to_check=[primary.id, hidden.id, added_later.id]
    ) == {hidden.id, added_later.id}
    assert (
        view_type.get_hidden_fields(fresh_view(), field_ids_to_check=[shown.id])
        == set()
    )

    only_always_visible = fresh_view()
    with django_assert_num_queries(2):
        assert (
            view_type.get_hidden_fields(
                only_always_visible, field_ids_to_check=[status.id, cover.id]
            )
            == set()
        )

    every_field = fresh_view()
    with django_assert_num_queries(3):
        assert view_type.get_hidden_fields(every_field) == {hidden.id, added_later.id}
