"""Tests for the fork's grouped aggregation service.

This is the service behind every dashboard chart: it returns one number per
bucket, which the core `local_jadawel_aggregate_rows` service cannot do.
"""

from django.http import HttpRequest

import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError

from arabase.integrations.local_jadawel.service_types import (
    LocalJadawelGroupedAggregateRowsUserServiceType,
)
from jadawel.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from jadawel.contrib.dashboard.data_sources.models import DashboardDataSource
from jadawel.contrib.dashboard.data_sources.service import DashboardDataSourceService
from jadawel.contrib.dashboard.widgets.service import WidgetService
from jadawel.contrib.database.rows.handler import RowHandler
from jadawel.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)
from jadawel.core.services.registries import service_type_registry


@pytest.fixture
def chart_setup(data_fixture):
    """A dashboard with a chart widget whose data source points at a table of
    three orders across two regions."""

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    amount_field = data_fixture.create_number_field(table=table, name="Amount")
    region_field = data_fixture.create_text_field(table=table, name="Region")
    RowHandler().create_rows(
        user,
        table,
        [
            {f"field_{amount_field.id}": 10, f"field_{region_field.id}": "Riyadh"},
            {f"field_{amount_field.id}": 20, f"field_{region_field.id}": "Riyadh"},
            {f"field_{amount_field.id}": 5, f"field_{region_field.id}": "Jeddah"},
        ],
    )

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_local_jadawel_integration(
        authorized_user=user, application=dashboard
    )
    widget = WidgetService().create_widget(
        user, "chart", dashboard.id, title="Orders", description=""
    )

    return {
        "user": user,
        "table": table,
        "amount_field": amount_field,
        "region_field": region_field,
        "dashboard": dashboard,
        "widget": widget,
    }


def configure(setup, **kwargs):
    service_type = service_type_registry.get(
        LocalJadawelGroupedAggregateRowsUserServiceType.type
    )
    DashboardDataSourceService().update_data_source(
        setup["user"], setup["widget"].data_source_id, service_type, **kwargs
    )
    return setup["widget"].data_source


def reload_service(setup):
    return DashboardDataSource.objects.get(
        id=setup["widget"].data_source_id
    ).service.specific


def dispatch(setup):
    dispatch_context = DashboardDispatchContext(HttpRequest(), setup["widget"])
    return DashboardDataSourceService().dispatch_data_source(
        setup["user"], setup["widget"].data_source_id, dispatch_context
    )


@pytest.mark.django_db
def test_dispatch_groups_by_a_field(chart_setup):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {
                "field_id": chart_setup["amount_field"].id,
                "aggregation_type": "sum",
            }
        ],
        service_aggregation_group_bys=[{"field_id": chart_setup["region_field"].id}],
    )

    result = dispatch(chart_setup)["result"]

    # The default sort is the first series descending, so Riyadh (30) leads.
    assert [group["value"] for group in result["groups"]] == ["Riyadh", "Jeddah"]
    assert len(result["series"]) == 1
    assert result["series"][0]["data"] == ["30", "5"]
    assert result["truncated"] is False


@pytest.mark.django_db
def test_dispatch_without_a_group_by_returns_one_bucket(chart_setup):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"}
        ],
        service_aggregation_group_bys=[],
    )

    result = dispatch(chart_setup)["result"]

    assert result["groups"] == []
    assert result["series"][0]["data"] == ["35"]


@pytest.mark.django_db
def test_dispatch_with_multiple_series(chart_setup):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"},
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "max"},
        ],
        service_aggregation_group_bys=[{"field_id": chart_setup["region_field"].id}],
    )

    result = dispatch(chart_setup)["result"]

    keys = [series["key"] for series in result["series"]]
    assert keys == [
        f"field_{chart_setup['amount_field'].id}_sum",
        f"field_{chart_setup['amount_field'].id}_max",
    ]
    assert result["series"][0]["data"] == ["30", "5"]
    assert result["series"][1]["data"] == ["20", "5"]


@pytest.mark.django_db
def test_dispatch_without_series_raises(chart_setup):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[],
    )

    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        dispatch(chart_setup)


@pytest.mark.django_db
def test_dispatch_skips_a_trashed_series_field(chart_setup, data_fixture):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"}
        ],
    )
    chart_setup["amount_field"].trashed = True
    chart_setup["amount_field"].save()

    # A trashed field leaves no usable series, which is a configuration problem
    # rather than a crash.
    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        dispatch(chart_setup)


@pytest.mark.django_db
def test_bucket_cap_is_applied(chart_setup, settings):
    settings.ARABASE_CHART_MAX_BUCKETS = 1
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"}
        ],
        service_aggregation_group_bys=[{"field_id": chart_setup["region_field"].id}],
    )

    result = dispatch(chart_setup)["result"]

    assert len(result["groups"]) == 1
    assert result["truncated"] is True


@pytest.mark.django_db
def test_group_by_single_select_resolves_labels_and_colors(data_fixture, chart_setup):
    select_field = data_fixture.create_single_select_field(
        table=chart_setup["table"], name="Status"
    )
    option = data_fixture.create_select_option(
        field=select_field, value="Open", color="blue"
    )
    row = chart_setup["table"].get_model().objects.first()
    setattr(row, f"field_{select_field.id}_id", option.id)
    row.save()

    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"}
        ],
        service_aggregation_group_bys=[{"field_id": select_field.id}],
    )

    result = dispatch(chart_setup)["result"]

    assert {"value": "Open", "color": "blue"} in result["groups"]


@pytest.mark.django_db
def test_too_many_series_is_rejected(chart_setup, data_fixture):
    fields = [
        data_fixture.create_number_field(table=chart_setup["table"]) for _ in range(6)
    ]

    with pytest.raises(DRFValidationError):
        configure(
            chart_setup,
            table_id=chart_setup["table"].id,
            service_aggregation_series=[
                {"field_id": field.id, "aggregation_type": "sum"} for field in fields
            ],
        )


@pytest.mark.django_db
def test_duplicate_series_is_rejected(chart_setup):
    with pytest.raises(DRFValidationError):
        configure(
            chart_setup,
            table_id=chart_setup["table"].id,
            service_aggregation_series=[
                {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"},
                {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"},
            ],
        )


@pytest.mark.django_db
def test_more_than_one_group_by_is_rejected(chart_setup):
    with pytest.raises(DRFValidationError):
        configure(
            chart_setup,
            table_id=chart_setup["table"].id,
            service_aggregation_group_bys=[
                {"field_id": chart_setup["region_field"].id},
                {"field_id": chart_setup["amount_field"].id},
            ],
        )


@pytest.mark.django_db
def test_changing_the_table_drops_series_and_group_bys(chart_setup, data_fixture):
    configure(
        chart_setup,
        table_id=chart_setup["table"].id,
        service_aggregation_series=[
            {"field_id": chart_setup["amount_field"].id, "aggregation_type": "sum"}
        ],
        service_aggregation_group_bys=[{"field_id": chart_setup["region_field"].id}],
    )
    other_table = data_fixture.create_database_table(
        database=chart_setup["table"].database
    )

    configure(chart_setup, table_id=other_table.id)

    service = reload_service(chart_setup)
    assert service.service_aggregation_series.count() == 0
    assert service.service_aggregation_group_bys.count() == 0
