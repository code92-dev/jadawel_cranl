import json

from django.shortcuts import reverse

import pytest
from pytest_unordered import unordered
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)

from jadawel.contrib.database.views.handler import ViewHandler


def _get_only_page(response):
    response_json = response.json()
    assert set(response_json.keys()) == {"pages"}
    assert len(response_json["pages"]) == 1
    return response_json["pages"][0]


def _get_page_by_parent(response_json, parent):
    for page in response_json["pages"]:
        if page["parent"] == parent:
            return page
    pytest.fail(f"Could not find group-by data page for parent {parent}")


def _assert_value_not_leaked(response_json, values, field_ids=()):
    dumped = json.dumps(response_json)
    for value in values:
        assert value not in dumped
    for field_id in field_ids:
        assert f"field_{field_id}" not in dumped


@pytest.mark.django_db
def test_public_group_by_data_saved_hidden_group_by_returns_empty_shape(
    api_client, data_fixture
):
    """
    A saved group-by on a hidden field must not be honored by the public
    group-by data endpoint: the visitor sees the ungrouped (empty) shape and
    never the hidden field's raw values.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden)

    model = table.get_model()
    model.objects.create(**{f"field_{hidden.id}": "secret-x"})
    model.objects.create(**{f"field_{hidden.id}": "secret-y"})

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK
    page = _get_only_page(response)
    assert page["groups"] == []
    assert page["group_count"] == 0
    _assert_value_not_leaked(response.json(), ["secret-x", "secret-y"], [hidden.id])


@pytest.mark.django_db
def test_public_group_by_data_hidden_first_visible_second_only_exposes_visible_level(
    api_client, data_fixture
):
    """
    With a hidden group-by saved before a visible one, only the visible field's
    level may appear in the response.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    visible = data_fixture.create_text_field(table=table, name="Visible")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden, order="ASC")
    data_fixture.create_view_group_by(view=grid, field=visible, order="ASC")

    model = table.get_model()
    model.objects.create(
        **{f"field_{hidden.id}": "secret-x", f"field_{visible.id}": "Alpha"}
    )
    model.objects.create(
        **{f"field_{hidden.id}": "secret-y", f"field_{visible.id}": "Alpha"}
    )
    model.objects.create(
        **{f"field_{hidden.id}": "secret-z", f"field_{visible.id}": "Beta"}
    )

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK
    page = _get_only_page(response)
    assert page["group_count"] == 2
    assert [group["path"][f"field_{visible.id}"] for group in page["groups"]] == [
        "Alpha",
        "Beta",
    ]
    assert [group["row_count"] for group in page["groups"]] == [2, 1]
    for group in page["groups"]:
        assert set(group["path"].keys()) == {f"field_{visible.id}"}
    _assert_value_not_leaked(
        response.json(), ["secret-x", "secret-y", "secret-z"], [hidden.id]
    )


@pytest.mark.django_db
def test_public_group_by_data_hidden_middle_level_is_skipped(
    api_client, data_fixture
):
    """
    visible-first + hidden-middle + visible-third: the hidden level must be
    removed from the hierarchy so depth 1 groups directly by the third field,
    with row counts and per-group aggregations on visible fields intact.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible_1 = data_fixture.create_text_field(table=table, name="VisibleOne")
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    visible_2 = data_fixture.create_text_field(table=table, name="VisibleTwo")
    amount = data_fixture.create_number_field(
        table=table, name="Amount", number_decimal_places=0
    )
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=visible_1, order="ASC")
    data_fixture.create_view_group_by(view=grid, field=hidden, order="ASC")
    data_fixture.create_view_group_by(view=grid, field=visible_2, order="ASC")
    ViewHandler().update_field_options(
        view=grid,
        field_options={
            amount.id: {"aggregation_type": "sum", "aggregation_raw_type": "sum"}
        },
    )

    model = table.get_model()
    model.objects.create(
        **{
            f"field_{visible_1.id}": "A",
            f"field_{hidden.id}": "secret-x",
            f"field_{visible_2.id}": "p",
            f"field_{amount.id}": 10,
        }
    )
    model.objects.create(
        **{
            f"field_{visible_1.id}": "A",
            f"field_{hidden.id}": "secret-y",
            f"field_{visible_2.id}": "p",
            f"field_{amount.id}": 20,
        }
    )
    model.objects.create(
        **{
            f"field_{visible_1.id}": "B",
            f"field_{hidden.id}": "secret-x",
            f"field_{visible_2.id}": "q",
            f"field_{amount.id}": 40,
        }
    )

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url, {"depth": "1"})

    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    page_a = _get_page_by_parent(response_json, {f"field_{visible_1.id}": "A"})
    assert page_a["group_count"] == 1
    group_a = page_a["groups"][0]
    # The hidden middle level is removed, so the depth-1 group's path runs
    # through the visible levels only: the parent prefix plus its own value.
    assert group_a["path"] == {
        f"field_{visible_1.id}": "A",
        f"field_{visible_2.id}": "p",
    }
    assert group_a["row_count"] == 2
    assert group_a["aggregations"] == {f"field_{amount.id}": 30}

    page_b = _get_page_by_parent(response_json, {f"field_{visible_1.id}": "B"})
    assert page_b["group_count"] == 1
    group_b = page_b["groups"][0]
    assert group_b["path"] == {
        f"field_{visible_1.id}": "B",
        f"field_{visible_2.id}": "q",
    }
    assert group_b["row_count"] == 1
    assert group_b["aggregations"] == {f"field_{amount.id}": 40}

    _assert_value_not_leaked(response_json, ["secret-x", "secret-y"], [hidden.id])


@pytest.mark.django_db
def test_public_group_by_data_all_hidden_group_bys_returns_empty_shape(
    api_client, data_fixture
):
    """
    When every saved group-by level is hidden, the public endpoint must return
    the ungrouped (empty) shape.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    hidden_1 = data_fixture.create_text_field(table=table, name="HiddenOne")
    hidden_2 = data_fixture.create_text_field(table=table, name="HiddenTwo")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden_1, hidden=True)
    data_fixture.create_grid_view_field_option(grid, hidden_2, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden_1, order="ASC")
    data_fixture.create_view_group_by(view=grid, field=hidden_2, order="ASC")

    model = table.get_model()
    model.objects.create(
        **{f"field_{hidden_1.id}": "secret-x", f"field_{hidden_2.id}": "secret-y"}
    )

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK
    page = _get_only_page(response)
    assert page["groups"] == []
    assert page["group_count"] == 0
    _assert_value_not_leaked(
        response.json(), ["secret-x", "secret-y"], [hidden_1.id, hidden_2.id]
    )


@pytest.mark.django_db
def test_public_group_by_data_adhoc_hidden_group_by_without_saved_is_rejected(
    api_client, data_fixture
):
    """
    Regression guard (already secure): an explicit ad-hoc ``group_by`` naming a
    hidden field of a public view is rejected, even without any saved group-by.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible = data_fixture.create_text_field(table=table, name="Visible")
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=visible)

    model = table.get_model()
    model.objects.create(
        **{f"field_{visible.id}": "Alpha", f"field_{hidden.id}": "secret-x"}
    )

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url, {"group_by": f"field_{hidden.id}"})

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"


@pytest.mark.django_db
def test_public_password_protected_group_by_data_filters_saved_hidden_group_by(
    api_client, data_fixture
):
    """
    A password-protected public view applies the same saved-hidden-group-by
    filtering as the anonymous case.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    grid = data_fixture.create_grid_view(
        table=table, public=True, public_view_password="password"
    )
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden)

    model = table.get_model()
    model.objects.create(**{f"field_{hidden.id}": "secret-x"})

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url)
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"

    public_view_token = ViewHandler().encode_public_view_token(grid)
    response = api_client.get(
        url, HTTP_JADAWEL_VIEW_AUTHORIZATION=f"JWT {public_view_token}"
    )

    assert response.status_code == HTTP_200_OK
    page = _get_only_page(response)
    assert page["groups"] == []
    assert page["group_count"] == 0
    _assert_value_not_leaked(response.json(), ["secret-x"], [hidden.id])


@pytest.mark.django_db
def test_public_rows_adhoc_group_by_hidden_field_with_saved_group_by_is_rejected(
    api_client, data_fixture
):
    """
    A saved group-by on a hidden field must not taint the visible field set of
    the public rows endpoint: an explicit ``group_by`` naming the hidden field
    must be rejected instead of leaking its values through the ordering and
    ``group_by_metadata``.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible = data_fixture.create_text_field(table=table, name="Visible")
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden, order="ASC")

    model = table.get_model()
    model.objects.create(
        **{f"field_{visible.id}": "Alpha", f"field_{hidden.id}": "secret-x"}
    )

    url = reverse("api:database:views:grid:public_rows", kwargs={"slug": grid.slug})
    response = api_client.get(
        f"{url}?group_by=field_{hidden.id}&include=group_by_metadata"
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ORDER_BY_FIELD_NOT_FOUND"
    assert "group_by_metadata" not in response.json()


@pytest.mark.django_db
def test_public_rows_group_by_visible_field_with_saved_hidden_group_by(
    api_client, data_fixture
):
    """
    Grouping the public rows endpoint by a visible field while a hidden
    group-by is saved must order and report metadata only on the visible
    field, and must not include the hidden field's values in the rows.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    visible = data_fixture.create_text_field(table=table, name="Visible")
    hidden = data_fixture.create_text_field(table=table, name="Hidden")
    grid = data_fixture.create_grid_view(table=table, public=True)
    data_fixture.create_grid_view_field_option(grid, hidden, hidden=True)
    data_fixture.create_view_group_by(view=grid, field=hidden, order="ASC")

    model = table.get_model()
    first = model.objects.create(
        **{f"field_{visible.id}": "a", f"field_{hidden.id}": "secret-x"}
    )
    second = model.objects.create(
        **{f"field_{visible.id}": "b", f"field_{hidden.id}": "secret-y"}
    )
    third = model.objects.create(
        **{f"field_{visible.id}": "a", f"field_{hidden.id}": "secret-z"}
    )

    url = reverse("api:database:views:grid:public_rows", kwargs={"slug": grid.slug})
    response = api_client.get(
        f"{url}?group_by=field_{visible.id}&include=group_by_metadata"
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert [result["id"] for result in response_json["results"]] == [
        first.id,
        third.id,
        second.id,
    ]
    assert set(response_json["group_by_metadata"].keys()) == {f"field_{visible.id}"}
    assert response_json["group_by_metadata"][f"field_{visible.id}"] == unordered(
        [
            {"count": 2, f"field_{visible.id}": "a"},
            {"count": 1, f"field_{visible.id}": "b"},
        ]
    )
    for result in response_json["results"]:
        assert f"field_{hidden.id}" not in result
    _assert_value_not_leaked(response_json, ["secret-x", "secret-y", "secret-z"])


@pytest.mark.django_db
def test_public_group_by_data_five_saved_levels_and_limit_reached_on_sixth(
    api_client, data_fixture
):
    """
    Control: five visible saved group-by levels group normally on the public
    endpoint, and neither the API nor the ad-hoc path accepts a sixth level
    (MAX_GROUP_BYS).
    """

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    levels = [
        data_fixture.create_text_field(table=table, name=f"Level{i}")
        for i in range(1, 6)
    ]
    grid = data_fixture.create_grid_view(table=table, public=True)
    for field in levels:
        data_fixture.create_view_group_by(view=grid, field=field, order="ASC")

    model = table.get_model()
    model.objects.create(
        **{
            f"field_{levels[0].id}": "A",
            f"field_{levels[1].id}": "a",
            f"field_{levels[2].id}": "1",
            f"field_{levels[3].id}": "i",
            f"field_{levels[4].id}": "x",
        }
    )
    model.objects.create(
        **{
            f"field_{levels[0].id}": "A",
            f"field_{levels[1].id}": "a",
            f"field_{levels[2].id}": "1",
            f"field_{levels[3].id}": "ii",
            f"field_{levels[4].id}": "x",
        }
    )
    model.objects.create(
        **{
            f"field_{levels[0].id}": "A",
            f"field_{levels[1].id}": "b",
            f"field_{levels[2].id}": "2",
            f"field_{levels[3].id}": "i",
            f"field_{levels[4].id}": "x",
        }
    )
    model.objects.create(
        **{
            f"field_{levels[0].id}": "B",
            f"field_{levels[1].id}": "a",
            f"field_{levels[2].id}": "1",
            f"field_{levels[3].id}": "i",
            f"field_{levels[4].id}": "x",
        }
    )

    url = reverse(
        "api:database:views:grid:public-group-by-data", kwargs={"slug": grid.slug}
    )
    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK
    page = _get_only_page(response)
    assert page["group_count"] == 2
    assert [
        group["path"][f"field_{levels[0].id}"] for group in page["groups"]
    ] == ["A", "B"]
    assert [group["row_count"] for group in page["groups"]] == [3, 1]
    for group in page["groups"]:
        assert group["depth"] == 0

    sixth = data_fixture.create_text_field(table=table, name="Level6")
    data_fixture.create_grid_view_field_option(grid, sixth, hidden=False)

    response = api_client.post(
        reverse("api:database:views:list_group_bys", kwargs={"view_id": grid.id}),
        {"field": sixth.id, "order": "ASC"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_VIEW_GROUP_BY_LIMIT_REACHED"

    adhoc_group_by = ",".join(
        [f"field_{field.id}" for field in levels] + [f"field_{sixth.id}"]
    )
    response = api_client.get(url, {"group_by": adhoc_group_by})
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_VIEW_GROUP_BY_LIMIT_REACHED"
