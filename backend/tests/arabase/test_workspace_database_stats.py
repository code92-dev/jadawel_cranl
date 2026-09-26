"""Tests for the per-database counters behind the workspace home page.

Besides the payload, these pin the two table caps, the query budget and the exact
per-table `UNION ALL` statements both home page endpoints send, so the SQL stays
byte-identical when the builders are refactored.
"""

from contextlib import contextmanager
from datetime import date, timedelta

from django.db import connection
from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from arabase.api import activity, database_stats
from arabase.api.activity import get_workspace_activity
from arabase.api.database_stats import get_database_stats, visible_tables
from jadawel.contrib.database.table.models import Table


@contextmanager
def _captured_statements():
    """Every `(sql, params)` pair sent to the database, before interpolation."""

    captured = []

    def wrapper(execute, sql, params, many, context):
        captured.append((sql, params))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(wrapper):
        yield captured


def _row_count_statements(captured):
    return [(sql, params) for sql, params in captured if "AS row_count" in sql]


def _activity_statements(captured):
    return [(sql, params) for sql, params in captured if "AS per_table" in sql]


def _workspace_with_live_and_trashed_data(data_fixture):
    """Two databases holding tables, fields and rows, some of each trashed, and a
    third database holding nothing."""

    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    first = data_fixture.create_database_application(workspace=workspace)
    second = data_fixture.create_database_application(workspace=workspace)
    empty = data_fixture.create_database_application(workspace=workspace)

    people = data_fixture.create_database_table(database=first, order=1)
    data_fixture.create_text_field(table=people, name="Name", primary=True)
    data_fixture.create_text_field(table=people, name="Email")
    data_fixture.create_text_field(table=people, name="Old", trashed=True)
    people_model = people.get_model()
    for _ in range(3):
        people_model.objects.create()
    people_model.objects.create(trashed=True)

    projects = data_fixture.create_database_table(database=first, order=2)
    data_fixture.create_text_field(table=projects, name="Title", primary=True)
    projects_model = projects.get_model()
    projects_model.objects.create()
    projects_model.objects.create()

    tasks = data_fixture.create_database_table(database=second, order=1)
    data_fixture.create_text_field(table=tasks, name="Task", primary=True)
    tasks.get_model().objects.create()

    archived = data_fixture.create_database_table(
        database=second, order=2, trashed=True
    )
    data_fixture.create_text_field(table=archived, name="Archived", primary=True)
    archived_model = archived.get_model()
    for _ in range(4):
        archived_model.objects.create()

    return user, token, workspace, [first, second, empty]


@pytest.mark.django_db
def test_stats_count_only_live_tables_fields_and_rows(data_fixture):
    user, _, workspace, databases = _workspace_with_live_and_trashed_data(data_fixture)
    first, second, empty = databases

    result = get_database_stats(databases, visible_tables(user, workspace, databases))

    assert result == {
        first.id: {
            "table_count": 2,
            "field_count": 3,
            "row_count": 5,
            "rows_exact": True,
        },
        second.id: {
            "table_count": 1,
            "field_count": 1,
            "row_count": 1,
            "rows_exact": True,
        },
        empty.id: {
            "table_count": 0,
            "field_count": 0,
            "row_count": 0,
            "rows_exact": True,
        },
    }


@pytest.mark.django_db
def test_endpoint_returns_the_counters_of_every_database(api_client, data_fixture):
    _, token, workspace, databases = _workspace_with_live_and_trashed_data(data_fixture)
    first, second, empty = databases

    response = api_client.get(
        reverse(
            "api:arabase:workspace_database_stats",
            kwargs={"workspace_id": workspace.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        str(first.id): {
            "table_count": 2,
            "field_count": 3,
            "row_count": 5,
            "rows_exact": True,
        },
        str(second.id): {
            "table_count": 1,
            "field_count": 1,
            "row_count": 1,
            "rows_exact": True,
        },
        str(empty.id): {
            "table_count": 0,
            "field_count": 0,
            "row_count": 0,
            "rows_exact": True,
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize("cap,row_count,rows_exact", [(0, None, False), (1, 2, True)])
def test_row_counts_are_dropped_above_the_table_cap(
    data_fixture, monkeypatch, cap, row_count, rows_exact
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)
    model = table.get_model()
    model.objects.create()
    model.objects.create()

    monkeypatch.setattr(database_stats, "MAX_TABLES_FOR_EXACT_COUNTS", cap)
    tables = visible_tables(user, workspace, [database])
    with _captured_statements() as captured:
        result = get_database_stats([database], tables)

    assert result == {
        database.id: {
            "table_count": 1,
            "field_count": 1,
            "row_count": row_count,
            "rows_exact": rows_exact,
        }
    }
    # Above the cap the rows are not counted at all, not counted and discarded.
    assert len(_row_count_statements(captured)) == (1 if rows_exact else 0)


@pytest.mark.django_db
@pytest.mark.parametrize("cap,complete", [(0, False), (1, True)])
def test_activity_gives_up_above_the_table_cap(
    data_fixture, monkeypatch, cap, complete
):
    database = data_fixture.create_database_application()
    table = data_fixture.create_database_table(database=database)
    table.get_model().objects.create()

    monkeypatch.setattr(activity, "MAX_TABLES_FOR_ACTIVITY", cap)
    with _captured_statements() as captured:
        result = get_workspace_activity(Table.objects.filter(database=database), days=3)

    assert result["days"] == 3
    assert result["complete"] is complete
    if complete:
        assert result["total"] == 1
        assert len(result["series"]) == 3
        assert len(_activity_statements(captured)) == 1
    else:
        assert result["total"] == 0
        assert result["series"] == []
        assert _activity_statements(captured) == []


@pytest.mark.django_db
def test_stats_for_two_tables_take_three_queries(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    first = data_fixture.create_database_application(workspace=workspace)
    second = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=first)
    data_fixture.create_database_table(database=second)
    tables = visible_tables(user, workspace, [first, second])

    # The grouping, the field counts and one UNION ALL for every row count.
    with django_assert_num_queries(3):
        get_database_stats([first, second], tables)


@pytest.mark.django_db
def test_activity_for_two_tables_takes_two_queries(
    data_fixture, django_assert_num_queries
):
    database = data_fixture.create_database_application()
    data_fixture.create_database_table(database=database, order=1)
    data_fixture.create_database_table(database=database, order=2)
    tables = Table.objects.filter(database=database)

    # The table ids and one UNION ALL for every table's per-day counts.
    with django_assert_num_queries(2):
        get_workspace_activity(tables, days=7)


@pytest.mark.django_db
def test_row_counts_are_one_union_all_statement(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    first = data_fixture.create_database_application(workspace=workspace)
    second = data_fixture.create_database_application(workspace=workspace)
    a = data_fixture.create_database_table(database=first).id
    b = data_fixture.create_database_table(database=second).id
    tables = visible_tables(user, workspace, [first, second])

    with _captured_statements() as captured:
        get_database_stats([first, second], tables)

    assert _row_count_statements(captured) == [
        (
            f"SELECT {a} AS table_id, COUNT(*) AS row_count "
            f"FROM database_table_{a} WHERE trashed = false"
            " UNION ALL "
            f"SELECT {b} AS table_id, COUNT(*) AS row_count "
            f"FROM database_table_{b} WHERE trashed = false",
            None,
        )
    ]


@pytest.mark.django_db
def test_activity_is_one_union_all_statement_with_bound_dates(data_fixture):
    database = data_fixture.create_database_application()
    a = data_fixture.create_database_table(database=database, order=1).id
    b = data_fixture.create_database_table(database=database, order=2).id

    with _captured_statements() as captured:
        result = get_workspace_activity(Table.objects.filter(database=database), days=7)

    since = date.fromisoformat(result["series"][0]["date"])
    assert since == date.fromisoformat(result["series"][-1]["date"]) - timedelta(days=6)
    assert _activity_statements(captured) == [
        (
            "SELECT day, SUM(c) FROM ("
            "SELECT created_on::date AS day, COUNT(*) AS c "
            f"FROM database_table_{a} "
            "WHERE trashed = false AND created_on >= %s GROUP BY 1"
            " UNION ALL "
            "SELECT created_on::date AS day, COUNT(*) AS c "
            f"FROM database_table_{b} "
            "WHERE trashed = false AND created_on >= %s GROUP BY 1"
            ") AS per_table GROUP BY day",
            [since, since],
        )
    ]
