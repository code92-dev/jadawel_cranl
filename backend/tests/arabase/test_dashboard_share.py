"""Public link sharing for dashboards.

Mirrors the guarantees a shared form view gives: only someone who can edit the
application can create, rotate or revoke the link; anyone with the link can read
the dashboard; a password turns the link into a two-step flow; and the link
never becomes a way to reach a *different* dashboard's data.
"""

from datetime import timedelta

from django.db import connection
from django.http import HttpRequest
from django.shortcuts import reverse
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

import pytest
from freezegun import freeze_time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from arabase.dashboard.share.dispatch_context import get_public_allowed_properties
from arabase.dashboard.share.handler import DashboardShareHandler, token_lifetime
from arabase.dashboard.share.models import DashboardShare
from arabase.integrations.local_jadawel.service_types import (
    LocalJadawelGroupedAggregateRowsUserServiceType,
)
from jadawel.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.data_sources.models import DashboardDataSource
from jadawel.contrib.dashboard.data_sources.service import DashboardDataSourceService
from jadawel.contrib.dashboard.widgets.handler import WidgetHandler
from jadawel.contrib.dashboard.widgets.service import WidgetService
from jadawel.contrib.database.rows.handler import RowHandler
from jadawel.core.services.registries import service_type_registry


def share_url(dashboard):
    return reverse("api:arabase:dashboard_share", kwargs={"dashboard_id": dashboard.id})


def rotate_url(dashboard):
    return reverse(
        "api:arabase:dashboard_share_rotate_slug", kwargs={"dashboard_id": dashboard.id}
    )


def password_url(dashboard):
    return reverse(
        "api:arabase:dashboard_share_password", kwargs={"dashboard_id": dashboard.id}
    )


def public_url(slug):
    return reverse("api:arabase:public_dashboard", kwargs={"slug": slug})


def public_auth_url(slug):
    return reverse("api:arabase:public_dashboard_auth", kwargs={"slug": slug})


def dispatch_url(slug, data_source_id):
    return reverse(
        "api:arabase:public_dashboard_dispatch",
        kwargs={"slug": slug, "data_source_id": data_source_id},
    )


@pytest.mark.django_db
def test_create_share_returns_a_slug_and_is_idempotent(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)

    response = api_client.post(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_200_OK
    first = response.json()
    assert first["dashboard_id"] == dashboard.id
    assert first["slug"]
    assert first["has_password"] is False

    response = api_client.post(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["slug"] == first["slug"]
    assert DashboardShare.objects.filter(dashboard=dashboard).count() == 1


@pytest.mark.django_db
def test_get_share_is_null_until_the_dashboard_is_shared(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)

    response = api_client.get(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() is None

    DashboardShareHandler().create_share(dashboard)

    response = api_client.get(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_a_workspace_member_can_share(api_client, data_fixture):
    # `application.update` — the same bar a shared view uses — is granted to
    # every member of the workspace, not only to admins.
    admin = data_fixture.create_user()
    member, member_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)

    response = api_client.post(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {member_token}"}
    )
    assert response.status_code == HTTP_200_OK
    assert DashboardShare.objects.filter(dashboard=dashboard).exists()


@pytest.mark.django_db
def test_a_user_outside_the_workspace_cannot_share(api_client, data_fixture):
    data_fixture.create_user()
    outsider, outsider_token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application()

    response = api_client.post(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {outsider_token}"}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_rotating_the_slug_invalidates_the_previous_url(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    share = DashboardShareHandler().create_share(dashboard)
    old_slug = share.slug

    response = api_client.post(
        rotate_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_200_OK
    new_slug = response.json()["slug"]
    assert new_slug != old_slug

    assert api_client.get(public_url(old_slug)).status_code == HTTP_404_NOT_FOUND
    assert api_client.get(public_url(new_slug)).status_code == HTTP_200_OK


@pytest.mark.django_db
def test_deleting_the_share_revokes_the_link(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    slug = DashboardShareHandler().create_share(dashboard).slug

    response = api_client.delete(
        share_url(dashboard), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert api_client.get(public_url(slug)).status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_public_info_returns_the_dashboard_widgets_and_data_sources(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(
        workspace=workspace, name="Sales", description="Numbers"
    )
    data_source = (
        data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
            dashboard=dashboard
        )
    )
    widget = data_fixture.create_summary_widget(
        dashboard=dashboard, data_source=data_source, title="Total"
    )
    slug = DashboardShareHandler().create_share(dashboard).slug

    # No credentials at all: this is the anonymous visitor path.
    response = api_client.get(public_url(slug))
    assert response.status_code == HTTP_200_OK
    body = response.json()

    assert body["dashboard"] == {
        "id": dashboard.id,
        "name": "Sales",
        "description": "Numbers",
    }
    assert [w["id"] for w in body["widgets"]] == [widget.id]
    assert body["widgets"][0]["title"] == "Total"
    assert [d["id"] for d in body["data_sources"]] == [data_source.id]


@pytest.mark.django_db
def test_public_info_does_not_leak_the_workspace(api_client, data_fixture):
    dashboard = data_fixture.create_dashboard_application()
    slug = DashboardShareHandler().create_share(dashboard).slug

    body = api_client.get(public_url(slug)).json()

    assert set(body["dashboard"]) == {"id", "name", "description"}


@pytest.mark.django_db
def test_a_trashed_dashboard_is_not_publicly_reachable(api_client, data_fixture):
    dashboard = data_fixture.create_dashboard_application()
    slug = DashboardShareHandler().create_share(dashboard).slug

    dashboard.trashed = True
    dashboard.save()

    assert api_client.get(public_url(slug)).status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_password_protected_link_needs_a_token(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    slug = DashboardShareHandler().create_share(dashboard).slug

    response = api_client.patch(
        password_url(dashboard),
        {"password": "letmein-2026"},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["has_password"] is True

    response = api_client.get(public_url(slug))
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response.json()["error"]
        == "ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD"
    )

    response = api_client.post(
        public_auth_url(slug), {"password": "wrong"}, format="json"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = api_client.post(
        public_auth_url(slug), {"password": "letmein-2026"}, format="json"
    )
    assert response.status_code == HTTP_200_OK
    access_token = response.json()["access_token"]

    response = api_client.get(
        public_url(slug),
        **{"HTTP_JADAWEL_VIEW_AUTHORIZATION": f"JWT {access_token}"},
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_removing_the_password_reopens_the_link(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(dashboard), "letmein-2026")

    response = api_client.patch(
        password_url(dashboard),
        {"password": None},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["has_password"] is False
    assert api_client.get(public_url(share.slug)).status_code == HTTP_200_OK


@pytest.mark.django_db
def test_rotating_the_slug_invalidates_an_issued_password_token(
    api_client, data_fixture
):
    dashboard = data_fixture.create_dashboard_application()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(dashboard), "letmein-2026")
    access_token = handler.encode_token(share)

    handler.rotate_slug(share)

    response = api_client.get(
        public_url(share.slug),
        **{"HTTP_JADAWEL_VIEW_AUTHORIZATION": f"JWT {access_token}"},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_the_password_applies_to_the_owner_too(api_client, data_fixture):
    # A shared view lets a workspace member through on their session alone. A
    # dashboard must not: the owner would open their own protected link, never
    # be asked, and conclude the password does not work. Members still reach
    # the dashboard at /dashboard/<id> without a password.
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(dashboard), "letmein-2026")

    response = api_client.get(
        public_url(share.slug), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response.json()["error"]
        == "ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD"
    )

    # ... and the token issued for that password still lets them in.
    access_token = handler.encode_token(share)
    response = api_client.get(
        public_url(share.slug),
        **{
            "HTTP_AUTHORIZATION": f"JWT {token}",
            "HTTP_JADAWEL_VIEW_AUTHORIZATION": f"JWT {access_token}",
        },
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_password_change_is_rejected_when_the_dashboard_is_not_shared(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)

    response = api_client.patch(
        password_url(dashboard),
        {"password": "letmein-2026"},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_password_body_must_be_present(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    DashboardShareHandler().create_share(dashboard)

    response = api_client.patch(
        password_url(dashboard),
        {},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_dispatch_refuses_a_data_source_from_another_dashboard(
    api_client, data_fixture
):
    shared = data_fixture.create_dashboard_application()
    other = data_fixture.create_dashboard_application()
    foreign_data_source = (
        data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
            dashboard=other
        )
    )
    slug = DashboardShareHandler().create_share(shared).slug

    response = api_client.post(dispatch_url(slug, foreign_data_source.id))

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_dispatch_returns_the_aggregation_for_an_anonymous_visitor(
    api_client, data_fixture
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_number_field(table=table, name="Amount")
    model = table.get_model()
    model.objects.create(**{f"field_{field.id}": 10})
    model.objects.create(**{f"field_{field.id}": 32})

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    integration = data_fixture.create_local_jadawel_integration(
        application=dashboard, user=user
    )
    data_source = (
        data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
            dashboard=dashboard,
            integration=integration,
            table=table,
            field=field,
            aggregation_type="sum",
        )
    )
    slug = DashboardShareHandler().create_share(dashboard).slug

    response = api_client.post(dispatch_url(slug, data_source.id))

    assert response.status_code == HTTP_200_OK
    # `sum` over a number field comes back as a decimal string.
    assert response.json()["result"] == "42"


@pytest.mark.django_db
def test_dispatch_on_a_password_protected_link_needs_the_token(
    api_client, data_fixture
):
    dashboard = data_fixture.create_dashboard_application()
    data_source = (
        data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
            dashboard=dashboard
        )
    )
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(dashboard), "letmein-2026")

    response = api_client.post(dispatch_url(share.slug, data_source.id))

    assert response.status_code == HTTP_401_UNAUTHORIZED


# --- field scoping ---------------------------------------------------------
#
# A visitor is authorised to see the dashboard, which is the fields its widgets
# display. Serializing the dispatch result straight off the table model would
# hand them every other column of the same rows, so these tests pin the
# narrowing in both places it has to happen: the values in the dispatch, and
# the column names in the schema.


@pytest.fixture
def shared_records_list(data_fixture):
    """A shared dashboard whose one widget displays a single column."""

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    name_field = data_fixture.create_text_field(table=table, name="Name")
    salary_field = data_fixture.create_number_field(table=table, name="Salary")
    notes_field = data_fixture.create_text_field(table=table, name="Notes")

    RowHandler().create_rows(
        user,
        table,
        [
            {
                f"field_{name_field.id}": "Layla",
                f"field_{salary_field.id}": 90000,
                f"field_{notes_field.id}": "On probation",
            }
        ],
    )

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_local_jadawel_integration(
        authorized_user=user, application=dashboard
    )
    widget = WidgetService().create_widget(
        user,
        "records_list",
        dashboard.id,
        title="Team",
        description="",
        field_ids=[name_field.id],
    )
    DashboardDataSourceService().update_data_source(
        user,
        widget.data_source_id,
        service_type_registry.get("local_jadawel_list_rows"),
        table_id=table.id,
    )

    return {
        "user": user,
        "widget": widget,
        "dashboard": dashboard,
        "name_field": name_field,
        "salary_field": salary_field,
        "notes_field": notes_field,
        "slug": DashboardShareHandler().create_share(dashboard).slug,
    }


@pytest.mark.django_db
def test_public_dispatch_only_returns_the_displayed_fields(
    api_client, shared_records_list
):
    setup = shared_records_list

    response = api_client.post(
        dispatch_url(setup["slug"], setup["widget"].data_source_id)
    )

    assert response.status_code == HTTP_200_OK
    rows = response.json()["results"]
    assert len(rows) == 1
    # The widget displays Name. Salary and Notes belong to the same rows and
    # must not travel with them.
    assert rows[0]["Name"] == "Layla"
    assert "Salary" not in rows[0]
    assert "Notes" not in rows[0]


@pytest.mark.django_db
def test_public_info_schema_only_names_the_displayed_fields(
    api_client, shared_records_list
):
    setup = shared_records_list

    body = api_client.get(public_url(setup["slug"])).json()

    (data_source,) = body["data_sources"]
    properties = data_source["schema"]["items"]["properties"]
    assert f"field_{setup['name_field'].id}" in properties
    # Hiding the values but publishing the column names would still disclose
    # what the table holds.
    assert f"field_{setup['salary_field'].id}" not in properties
    assert f"field_{setup['notes_field'].id}" not in properties


@pytest.mark.django_db
def test_public_info_does_not_leak_the_service_configuration(
    api_client, shared_records_list
):
    body = api_client.get(public_url(shared_records_list["slug"])).json()

    (data_source,) = body["data_sources"]
    assert set(data_source) == {
        "id",
        "type",
        "schema",
        "name",
        "dashboard_id",
        "order",
        "date_field_id",
    }


@pytest.mark.django_db
def test_a_member_still_reads_every_field(shared_records_list):
    """The narrowing is for visitors only.

    Someone who can already open the table loses nothing, so a regression that
    restricted the authenticated path too would be caught here rather than in a
    bug report about missing columns.
    """

    setup = shared_records_list

    result = DashboardDataSourceService().dispatch_data_source(
        setup["user"],
        setup["widget"].data_source_id,
        DashboardDispatchContext(HttpRequest(), setup["widget"]),
    )

    assert set(result["results"][0]) >= {"Name", "Salary", "Notes"}


@pytest.mark.django_db
def test_an_empty_field_list_falls_back_to_the_first_columns(api_client, data_fixture):
    """An unconfigured widget renders the first few columns.

    The frontend resolves that fallback off the schema, so the backend has to
    resolve it the same way — otherwise the widget would render columns the
    dispatch refuses to return.
    """

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    # The fixture defaults every directly-created field to order 0. Give these
    # fields the distinct ordering that real fields receive so the schema's
    # "first three" is deterministic on PostgreSQL.
    first = data_fixture.create_text_field(table=table, name="First", order=0)
    second = data_fixture.create_text_field(table=table, name="Second", order=1)
    third = data_fixture.create_text_field(table=table, name="Third", order=2)
    fourth = data_fixture.create_text_field(table=table, name="Fourth", order=3)
    RowHandler().create_rows(
        user,
        table,
        [
            {
                f"field_{first.id}": "a",
                f"field_{second.id}": "b",
                f"field_{third.id}": "c",
                f"field_{fourth.id}": "d",
            }
        ],
    )

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_local_jadawel_integration(
        authorized_user=user, application=dashboard
    )
    widget = WidgetService().create_widget(
        user, "records_list", dashboard.id, title="Rows", description=""
    )
    DashboardDataSourceService().update_data_source(
        user,
        widget.data_source_id,
        service_type_registry.get("local_jadawel_list_rows"),
        table_id=table.id,
    )
    assert widget.field_ids == []
    slug = DashboardShareHandler().create_share(dashboard).slug

    row = api_client.post(dispatch_url(slug, widget.data_source_id)).json()["results"][
        0
    ]

    # `id` and `order` are row metadata rather than columns of the table.
    assert set(row) == {"id", "order", "First", "Second", "Third"}
    assert "Fourth" not in row


# --- allow-list scope ------------------------------------------------------
#
# The dispatch view needs only the entry of the data source it dispatches, and
# the info view already holds the dashboard's widgets and data sources. Either
# way the entries must be exactly the ones the whole-dashboard map holds.


def allowed(*fields):
    return ["result"] + [
        f"field_{field_id}" for field_id in sorted(f.id for f in fields)
    ]


@pytest.fixture
def shared_three_sources(data_fixture):
    """A shared dashboard with one data source of each allow-list shape: a
    records list naming its fields, a records list falling back to the first
    columns, and a chart whose service names the fields it aggregates."""

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    first = data_fixture.create_text_field(table=table, name="First", order=0)
    second = data_fixture.create_text_field(table=table, name="Second", order=1)
    third = data_fixture.create_text_field(table=table, name="Third", order=2)
    fourth = data_fixture.create_text_field(table=table, name="Fourth", order=3)
    amount = data_fixture.create_number_field(table=table, name="Amount", order=4)
    RowHandler().create_rows(
        user,
        table,
        [{f"field_{second.id}": "Riyadh", f"field_{amount.id}": 7}],
    )

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_local_jadawel_integration(
        authorized_user=user, application=dashboard
    )
    list_rows = service_type_registry.get("local_jadawel_list_rows")

    explicit = WidgetService().create_widget(
        user,
        "records_list",
        dashboard.id,
        title="Explicit",
        description="",
        field_ids=[fourth.id],
    )
    DashboardDataSourceService().update_data_source(
        user, explicit.data_source_id, list_rows, table_id=table.id
    )

    fallback = WidgetService().create_widget(
        user, "records_list", dashboard.id, title="Fallback", description=""
    )
    DashboardDataSourceService().update_data_source(
        user, fallback.data_source_id, list_rows, table_id=table.id
    )

    chart = WidgetService().create_widget(
        user, "chart", dashboard.id, title="Chart", description=""
    )
    DashboardDataSourceService().update_data_source(
        user,
        chart.data_source_id,
        service_type_registry.get(LocalJadawelGroupedAggregateRowsUserServiceType.type),
        table_id=table.id,
        service_aggregation_series=[{"field_id": amount.id, "aggregation_type": "sum"}],
        service_aggregation_group_bys=[{"field_id": second.id}],
    )

    def service_id(widget):
        return DashboardDataSource.objects.get(id=widget.data_source_id).service_id

    return {
        "user": user,
        "dashboard": dashboard,
        "data_source_ids": [
            explicit.data_source_id,
            fallback.data_source_id,
            chart.data_source_id,
        ],
        "chart_data_source_id": chart.data_source_id,
        "expected": {
            service_id(explicit): allowed(fourth),
            service_id(fallback): allowed(first, second, third),
            service_id(chart): allowed(second, amount),
        },
        "slug": DashboardShareHandler().create_share(dashboard).slug,
    }


@pytest.mark.django_db
def test_the_whole_dashboard_allow_list_is_unchanged(shared_three_sources):
    setup = shared_three_sources

    assert get_public_allowed_properties(setup["dashboard"]) == setup["expected"]


@pytest.mark.django_db
def test_the_allow_list_of_one_data_source_matches_the_whole_dashboard(
    shared_three_sources,
):
    setup = shared_three_sources
    dashboard = setup["dashboard"]
    full = get_public_allowed_properties(dashboard)

    for data_source_id in setup["data_source_ids"]:
        # Loaded the way the dispatch view loads it: the service is the generic
        # row rather than the specific one the info view's list holds.
        data_source = DashboardDataSourceHandler().get_data_source(data_source_id)

        assert get_public_allowed_properties(dashboard, data_sources=[data_source]) == {
            data_source.service_id: full[data_source.service_id]
        }


@pytest.mark.django_db
def test_the_allow_list_from_already_fetched_lists_matches(shared_three_sources):
    setup = shared_three_sources
    dashboard = setup["dashboard"]

    assert (
        get_public_allowed_properties(
            dashboard,
            widgets=WidgetHandler().get_widgets(dashboard),
            data_sources=DashboardDataSourceHandler().get_data_sources(dashboard),
        )
        == setup["expected"]
    )


@pytest.mark.django_db
def test_public_dispatch_queries_do_not_grow_with_the_data_sources(
    api_client, shared_three_sources
):
    setup = shared_three_sources
    url = dispatch_url(setup["slug"], setup["chart_data_source_id"])
    # Warm the table model and content type caches, so both measurements start
    # from the same state.
    assert api_client.post(url).status_code == HTTP_200_OK

    with CaptureQueriesContext(connection) as fewer:
        assert api_client.post(url).status_code == HTTP_200_OK

    for title in ("More", "Even more"):
        WidgetService().create_widget(
            setup["user"], "chart", setup["dashboard"].id, title=title, description=""
        )

    with CaptureQueriesContext(connection) as more:
        response = api_client.post(url)

    assert response.status_code == HTTP_200_OK
    assert response.json()["result"]["series"][0]["data"] == ["7"]
    assert len(more.captured_queries) == len(fewer.captured_queries)


# --- password and token hardening ------------------------------------------


@pytest.mark.django_db
def test_a_short_share_password_is_rejected(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    DashboardShareHandler().create_share(dashboard)

    response = api_client.patch(
        password_url(dashboard),
        {"password": "short"},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_auth_on_an_unprotected_link_does_not_hand_out_a_token(
    api_client, data_fixture
):
    """The link is already open, so this leaks no access — but an endpoint that
    reports success for a password it never checked is a lie in the audit log."""

    dashboard = data_fixture.create_dashboard_application()
    slug = DashboardShareHandler().create_share(dashboard).slug

    response = api_client.post(
        public_auth_url(slug), {"password": "anything at all"}, format="json"
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_a_share_token_expires(data_fixture):
    dashboard = data_fixture.create_dashboard_application()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(dashboard), "letmein-2026")

    token = handler.encode_token(share)
    assert handler.is_token_valid(share, token) is True
    assert "exp" in handler.decode_token(share, token)

    # Rotation revokes every token at once, which is no help against one that
    # has leaked out of a single visitor's browser. Expiry bounds that.
    with freeze_time(timezone.now() + token_lifetime() + timedelta(minutes=1)):
        assert handler.is_token_valid(share, token) is False
