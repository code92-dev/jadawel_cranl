"""The text widget and the chart and progress styles added with the dashboard
redesign (docs/DASHBOARD_REDESIGN.md)."""

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from arabase.dashboard.widgets.models import TextWidget
from jadawel.contrib.dashboard.application_types import DashboardApplicationType
from jadawel.contrib.dashboard.data_sources.models import DashboardDataSource
from jadawel.contrib.dashboard.widgets.models import Widget
from jadawel.contrib.dashboard.widgets.service import WidgetService
from jadawel.core.registries import ImportExportConfig


def create(api_client, token, dashboard, **values):
    return api_client.post(
        reverse("api:dashboard:widgets:list", kwargs={"dashboard_id": dashboard.id}),
        values,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )


@pytest.mark.django_db
def test_text_widget_owns_no_data_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)

    response = create(
        api_client,
        token,
        dashboard,
        type="text",
        title="المبيعات",
        body="الأرقام حتى نهاية الربع.\nتُحدَّث يوميًا.",
        text_style="section",
        width=12,
        height=1,
    )

    data = response.json()
    assert response.status_code == HTTP_200_OK, data
    assert data["text_style"] == "section"
    assert data["body"].endswith("تُحدَّث يوميًا.")
    assert "data_source_id" not in data
    assert DashboardDataSource.objects.count() == 0
    assert TextWidget.objects.get(id=data["id"]).height == 1


@pytest.mark.django_db
def test_text_widget_defaults_to_a_note_and_rejects_unknown_styles(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)

    note = create(api_client, token, dashboard, type="text", title="How to read")
    assert note.json()["text_style"] == "note"
    assert note.json()["body"] == ""

    bad = create(
        api_client, token, dashboard, type="text", title="x", text_style="banner"
    )
    assert bad.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_text_widget_survives_export_and_import(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    WidgetService().create_widget(
        user,
        "text",
        dashboard.id,
        title="Notes",
        body="Line one\nLine two",
        text_style="callout",
        appearance={"color": "yellow", "icon": "light-bulb"},
    )

    serialized = DashboardApplicationType().export_serialized(
        dashboard, ImportExportConfig(include_permission_data=True)
    )
    imported = DashboardApplicationType().import_serialized(
        workspace, serialized, ImportExportConfig(include_permission_data=True), {}
    )

    widget = Widget.objects.get(dashboard=imported).specific
    assert isinstance(widget, TextWidget)
    assert (widget.body, widget.text_style) == ("Line one\nLine two", "callout")
    assert widget.appearance == {"color": "yellow", "icon": "light-bulb"}


@pytest.mark.django_db
@pytest.mark.parametrize("chart_type", ["horizontal_bar", "area"])
def test_chart_widget_accepts_the_new_chart_types(api_client, data_fixture, chart_type):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)

    response = create(
        api_client, token, dashboard, type="chart", title="C", chart_type=chart_type
    )

    assert response.status_code == HTTP_200_OK, response.json()
    assert response.json()["chart_type"] == chart_type


@pytest.mark.django_db
def test_progress_widget_accepts_a_gauge(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    dashboard = data_fixture.create_dashboard_application(user=user)

    response = create(
        api_client,
        token,
        dashboard,
        type="progress",
        title="P",
        display_style="gauge",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    assert response.json()["display_style"] == "gauge"
