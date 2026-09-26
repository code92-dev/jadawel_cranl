"""Tests for the workspace activity series behind the home page chart."""

from datetime import timedelta

from django.shortcuts import reverse
from django.utils import timezone

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from arabase.api.activity import MAX_DAYS, get_workspace_activity
from jadawel.contrib.database.table.models import Table


def _set_created_on(model, row, when):
    """Backdate a row.

    `created_on` is `auto_now_add`, so it cannot be set on create and is ignored
    on a normal save. A queryset update writes the column directly.
    """

    model.objects.filter(id=row.id).update(created_on=when)


@pytest.mark.django_db
def test_series_is_dense_and_ordered_oldest_first(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    model = table.get_model()

    today = timezone.localdate()
    row = model.objects.create()
    _set_created_on(model, row, timezone.now() - timedelta(days=2))

    result = get_workspace_activity(Table.objects.filter(database=database), days=5)

    assert result["days"] == 5
    assert result["complete"] is True
    assert len(result["series"]) == 5

    dates = [point["date"] for point in result["series"]]
    assert dates == sorted(dates), "series must be ordered oldest first"
    assert dates[-1] == today.isoformat()

    # A quiet day is present with a zero, not omitted. A sparse series would make
    # the chart interpolate across it and read as steady activity.
    counts = {point["date"]: point["count"] for point in result["series"]}
    assert counts[(today - timedelta(days=2)).isoformat()] == 1
    assert counts[today.isoformat()] == 0
    assert result["total"] == 1


@pytest.mark.django_db
def test_counts_span_tables_and_databases_but_skip_trashed_rows(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    first = data_fixture.create_database_application(workspace=workspace)
    second = data_fixture.create_database_application(workspace=workspace)
    table_a = data_fixture.create_database_table(database=first)
    table_b = data_fixture.create_database_table(database=second)

    model_a = table_a.get_model()
    model_b = table_b.get_model()
    model_a.objects.create()
    model_a.objects.create()
    model_b.objects.create()
    model_b.objects.create(trashed=True)

    result = get_workspace_activity(
        Table.objects.filter(database__in=[first, second]), days=1
    )

    assert result["total"] == 3, "trashed rows must not count as activity"


@pytest.mark.django_db
def test_rows_outside_the_window_are_excluded(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    model = table.get_model()

    inside = model.objects.create()
    outside = model.objects.create()
    _set_created_on(model, inside, timezone.now() - timedelta(days=1))
    _set_created_on(model, outside, timezone.now() - timedelta(days=40))

    result = get_workspace_activity(Table.objects.filter(database=database), days=7)

    assert result["total"] == 1


@pytest.mark.django_db
def test_window_is_clamped_and_empty_workspace_is_not_an_error(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)

    assert (
        get_workspace_activity(Table.objects.filter(database=database), days=0)["days"]
        == 1
    )
    assert (
        get_workspace_activity(Table.objects.filter(database=database), days=10_000)[
            "days"
        ]
        == MAX_DAYS
    )

    # No databases at all still has to produce a drawable series rather than an
    # empty response the chart would have to special-case.
    empty = get_workspace_activity(Table.objects.none(), days=3)
    assert empty["complete"] is True
    assert empty["total"] == 0
    assert len(empty["series"]) == 3


@pytest.mark.django_db
def test_endpoint_returns_series_for_a_member(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    table.get_model().objects.create()

    response = api_client.get(
        reverse(
            "api:arabase.api:workspace_activity", kwargs={"workspace_id": workspace.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    body = response.json()
    assert body["total"] == 1
    assert len(body["series"]) == body["days"] == 30


@pytest.mark.django_db
def test_endpoint_clamps_a_malformed_days_parameter(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)

    response = api_client.get(
        reverse(
            "api:arabase.api:workspace_activity", kwargs={"workspace_id": workspace.id}
        )
        + "?days=not-a-number",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, "a bad parameter is not a server error"
    assert response.json()["days"] == 30


@pytest.mark.django_db
def test_endpoint_refuses_a_workspace_the_user_is_not_in(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    other_workspace = data_fixture.create_workspace()

    response = api_client.get(
        reverse(
            "api:arabase.api:workspace_activity",
            kwargs={"workspace_id": other_workspace.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_endpoint_404s_for_a_workspace_that_does_not_exist(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:arabase.api:workspace_activity", kwargs={"workspace_id": 999999}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"
