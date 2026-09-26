"""Characterization tests for the grouped aggregation service and the widgets.

They pin what the chart service writes, exports and imports: the relation
payloads and their key order, the remapped series references, the queries an
update or an import sends, the sort defaults, the validation errors, and the
serializer overrides of the four data-source widgets. Refactoring those code
paths must leave every assertion here unchanged.
"""

import copy
import json
import re
from io import BytesIO

from django.db import connection
from django.http import HttpRequest
from django.test.utils import CaptureQueriesContext

import pytest
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from arabase.dashboard.widgets.models import ChartWidget
from arabase.dashboard.widgets.widget_types import (
    ChartWidgetType,
    ProgressWidgetType,
    RecordsListWidgetType,
    UpcomingDatesWidgetType,
)
from arabase.integrations.local_jadawel.models import (
    SORT_ON_GROUP_BY,
    SORT_ON_SERIES,
    LocalJadawelGroupedAggregateRows,
    LocalJadawelTableServiceAggregationSeries,
    LocalJadawelTableServiceAggregationSortBy,
)
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
from jadawel.core.handler import CoreHandler
from jadawel.core.registries import ImportExportConfig
from jadawel.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)
from jadawel.core.services.handler import ServiceHandler
from jadawel.core.services.registries import service_type_registry

SERIES = "service_aggregation_series"
GROUP_BYS = "service_aggregation_group_bys"
SORTS = "service_aggregation_sorts"

INTEGRATION_TABLE = "core_integration"
SERVICE_TABLE = "core_service"
FILTER_TABLE = "integrations_localjadaweltableservicefilter"
GROUPED_TABLE = "arabase_localjadawelgroupedaggregaterows"
SERIES_TABLE = "arabase_localjadaweltableserviceaggregationseries"
GROUP_BY_TABLE = "arabase_localjadaweltableserviceaggregationgroupby"
SORT_TABLE = "arabase_localjadaweltableserviceaggregationsortby"

# The statement sequences below were recorded on the code before the relation
# helpers were shared. A relation delete reads its rows first and sends no
# DELETE when there are none, because delete signals rule out a fast delete.
EXPORT_PREPARED_VALUES = [
    ("SELECT", SERIES_TABLE),
    ("SELECT", GROUP_BY_TABLE),
    ("SELECT", SORT_TABLE),
]
SAVE_SERVICE = [("UPDATE", SERVICE_TABLE), ("UPDATE", GROUPED_TABLE)]

_STATEMENT_TABLE = re.compile(r'\b(?:FROM|INTO|UPDATE)\s+"([^"]+)"', re.IGNORECASE)


def service_type():
    return service_type_registry.get(
        LocalJadawelGroupedAggregateRowsUserServiceType.type
    )


def statements(context):
    """`(verb, table)` for every statement a capture saw, in execution order."""

    result = []
    for query in context.captured_queries:
        sql = query["sql"].lstrip()
        match = _STATEMENT_TABLE.search(sql)
        result.append(
            (sql.split(None, 1)[0].upper(), match.group(1) if match else None)
        )
    return result


def ordered(entries):
    """The entries as lists of `(key, value)` pairs, so key order is compared."""

    return [list(entry.items()) for entry in entries]


def rows_of(service):
    return {
        "series": [
            (s.field_id, s.aggregation_type, s.order)
            for s in service.service_aggregation_series.all()
        ],
        "group_bys": [
            (g.field_id, g.order) for g in service.service_aggregation_group_bys.all()
        ],
        "sorts": [
            (s.sort_on, s.reference, s.direction, s.order)
            for s in service.service_aggregation_sorts.all()
        ],
    }


def fresh(service_id):
    return LocalJadawelGroupedAggregateRows.objects.get(id=service_id)


@pytest.fixture
def chart(data_fixture):
    """
    A chart over four orders in three regions, and a second table with the same
    three fields to move the chart onto. Sums per region: Riyadh 30 / 3 units,
    Jeddah 5 / 4 units, Dammam 5 / 1 unit.
    """

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(
        workspace=workspace, name="المبيعات"
    )
    table = data_fixture.create_database_table(database=database, name="Orders")
    amount = data_fixture.create_number_field(table=table, name="Amount")
    units = data_fixture.create_number_field(table=table, name="Units")
    region = data_fixture.create_text_field(table=table, name="Region")
    RowHandler().create_rows(
        user,
        table,
        [
            {amount.db_column: 10, units.db_column: 1, region.db_column: "Riyadh"},
            {amount.db_column: 20, units.db_column: 2, region.db_column: "Riyadh"},
            {amount.db_column: 5, units.db_column: 4, region.db_column: "Jeddah"},
            {amount.db_column: 5, units.db_column: 1, region.db_column: "Dammam"},
        ],
    )

    other_table = data_fixture.create_database_table(database=database, name="Other")
    other_amount = data_fixture.create_number_field(table=other_table, name="Amount")
    other_units = data_fixture.create_number_field(table=other_table, name="Units")
    other_region = data_fixture.create_text_field(table=other_table, name="Region")

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_local_jadawel_integration(
        authorized_user=user, application=dashboard
    )
    widget = WidgetService().create_widget(
        user,
        "chart",
        dashboard.id,
        title="Orders",
        description="",
        series_config={
            f"field_{amount.id}_sum": {"color": "blue"},
            f"field_{units.id}_sum": {"label": "الوحدات"},
            "not_a_series_key": {"color": "red"},
        },
    )

    setup = {
        "user": user,
        "workspace": workspace,
        "database": database,
        "table": table,
        "amount": amount,
        "units": units,
        "region": region,
        "other_table": other_table,
        "other_amount": other_amount,
        "other_units": other_units,
        "other_region": other_region,
        "dashboard": dashboard,
        "widget": widget,
    }
    configure(
        setup,
        table_id=table.id,
        service_aggregation_series=[
            {"field_id": amount.id, "aggregation_type": "sum"},
            {"field_id": units.id, "aggregation_type": "sum"},
        ],
        service_aggregation_group_bys=[{"field_id": region.id}],
        service_aggregation_sorts=[
            {
                "sort_on": SORT_ON_SERIES,
                "reference": f"field_{amount.id}_sum",
                "direction": "ASC",
            },
            {"sort_on": SORT_ON_GROUP_BY, "reference": "", "direction": "DESC"},
        ],
    )
    setup["service_id"] = DashboardDataSource.objects.get(
        id=widget.data_source_id
    ).service_id
    return setup


def configure(setup, widget=None, **kwargs):
    widget = widget or setup["widget"]
    DashboardDataSourceService().update_data_source(
        setup["user"], widget.data_source_id, service_type(), **kwargs
    )


def dispatch(setup):
    dispatch_context = DashboardDispatchContext(HttpRequest(), setup["widget"])
    return DashboardDataSourceService().dispatch_data_source(
        setup["user"], setup["widget"].data_source_id, dispatch_context
    )["result"]


# --- a. export / import round trip ------------------------------------------


@pytest.mark.django_db
def test_a_workspace_round_trip_remaps_the_series_group_bys_sorts_and_config(
    chart, data_fixture
):
    amount, units, region = chart["amount"], chart["units"], chart["region"]

    # The same per-application export export_workspace_applications runs,
    # without its repeatable-read transaction, which a test transaction refuses.
    config = ImportExportConfig(include_permission_data=False)
    exported = [
        application.get_type().export_serialized(application, config)
        for application in (
            a.specific for a in chart["workspace"].application_set.all()
        )
    ]
    # What goes into the file has to survive JSON unchanged.
    exported = json.loads(json.dumps(exported))

    exported_dashboard = next(a for a in exported if a["type"] == "dashboard")
    [exported_source] = exported_dashboard["data_sources"]
    exported_service = exported_source["service"]
    assert exported_service["type"] == "local_jadawel_grouped_aggregate_rows"
    assert exported_service["table_id"] == chart["table"].id
    assert ordered(exported_service[SERIES]) == [
        [("field_id", amount.id), ("aggregation_type", "sum")],
        [("field_id", units.id), ("aggregation_type", "sum")],
    ]
    assert ordered(exported_service[GROUP_BYS]) == [[("field_id", region.id)]]
    assert ordered(exported_service[SORTS]) == [
        [
            ("sort_on", "SERIES"),
            ("reference", f"field_{amount.id}_sum"),
            ("direction", "ASC"),
        ],
        [("sort_on", "GROUP_BY"), ("reference", ""), ("direction", "DESC")],
    ]
    [exported_widget] = exported_dashboard["widgets"]
    assert exported_widget["type"] == "chart"
    assert exported_widget["data_source_id"] == exported_source["id"]
    assert exported_widget["series_config"] == {
        f"field_{amount.id}_sum": {"color": "blue"},
        f"field_{units.id}_sum": {"label": "الوحدات"},
        "not_a_series_key": {"color": "red"},
    }

    target = data_fixture.create_workspace(user=chart["user"])
    imported, _ = CoreHandler().import_applications_to_workspace(
        target,
        exported,
        BytesIO(),
        ImportExportConfig(include_permission_data=False),
        None,
    )

    imported_database = next(a for a in imported if a.get_type().type == "database")
    imported_table = imported_database.table_set.get(name="Orders")
    new = {f.name: f.id for f in imported_table.field_set.all()}
    assert new["Amount"] != amount.id and new["Units"] != units.id

    imported_dashboard = next(a for a in imported if a.get_type().type == "dashboard")
    widget = ChartWidget.objects.get(dashboard=imported_dashboard)
    service = widget.data_source.service.specific

    assert service.table_id == imported_table.id
    assert rows_of(service) == {
        "series": [(new["Amount"], "sum", 0), (new["Units"], "sum", 1)],
        "group_bys": [(new["Region"], 0)],
        "sorts": [
            ("SERIES", f"field_{new['Amount']}_sum", "ASC", 0),
            ("GROUP_BY", "", "DESC", 1),
        ],
    }
    assert widget.series_config == {
        f"field_{new['Amount']}_sum": {"color": "blue"},
        f"field_{new['Units']}_sum": {"label": "الوحدات"},
        "not_a_series_key": {"color": "red"},
    }
    assert list(widget.series_config) == [
        f"field_{new['Amount']}_sum",
        f"field_{new['Units']}_sum",
        "not_a_series_key",
    ]


REMAP_CASES = [
    # (key, remapped key) with the mapping {1: 42}.
    ("field_1_sum", "field_42_sum"),
    ("field_1_percent_empty", "field_42_percent_empty"),
    ("field_1_", "field_42_"),
    ("field_99_sum", "field_99_sum"),
    ("field_1", "field_1"),
    ("field_x_sum", "field_x_sum"),
    ("Field_1_sum", "Field_1_sum"),
    ("xfield_1_sum", "xfield_1_sum"),
    ("", ""),
    ("not_a_series_key", "not_a_series_key"),
]


@pytest.mark.parametrize("key,expected", REMAP_CASES)
def test_series_references_and_series_config_keys_remap_the_same_way(key, expected):
    id_mapping = {"database_fields": {1: 42}}

    sorts = LocalJadawelGroupedAggregateRowsUserServiceType().deserialize_property(
        SORTS,
        [
            {"sort_on": SORT_ON_SERIES, "reference": key, "direction": "ASC"},
            {"sort_on": SORT_ON_GROUP_BY, "reference": key, "direction": "DESC"},
        ],
        id_mapping,
    )
    # Only a series sort's reference names a series; a group by sort's is kept.
    assert ordered(sorts) == [
        [("sort_on", "SERIES"), ("reference", expected), ("direction", "ASC")],
        [("sort_on", "GROUP_BY"), ("reference", key), ("direction", "DESC")],
    ]

    remapped = ChartWidgetType().deserialize_property(
        "series_config", {key: {"color": "blue"}}, id_mapping
    )
    assert remapped == {expected: {"color": "blue"}}


@pytest.mark.django_db
def test_deserializing_the_relations_keeps_the_entries_and_maps_the_field_ids():
    service_type = LocalJadawelGroupedAggregateRowsUserServiceType()
    id_mapping = {"database_fields": {1: 11, 2: 22}}

    series = service_type.deserialize_property(
        SERIES,
        [
            {"field_id": 1, "aggregation_type": "sum"},
            {"field_id": 3, "aggregation_type": "max"},
            {"field_id": None, "aggregation_type": ""},
        ],
        id_mapping,
    )
    # A field that was not exported maps to no field, and the entry stays.
    assert ordered(series) == [
        [("field_id", 11), ("aggregation_type", "sum")],
        [("field_id", None), ("aggregation_type", "max")],
        [("field_id", None), ("aggregation_type", "")],
    ]
    assert service_type.deserialize_property(
        GROUP_BYS, [{"field_id": 2}], id_mapping
    ) == [{"field_id": 22}]
    # A sort without a sort_on is not a series sort, so it is not remapped.
    assert service_type.deserialize_property(
        SORTS, [{"reference": "field_1_sum"}], id_mapping
    ) == [{"reference": "field_1_sum"}]
    for key in (SERIES, GROUP_BYS, SORTS):
        assert service_type.deserialize_property(key, None, id_mapping) == []
        assert service_type.deserialize_property(key, [], {}) == []
    assert ChartWidgetType().deserialize_property("series_config", {}, {}) == {}


# --- b. serialize_property and export_prepared_values -----------------------


@pytest.mark.django_db
def test_serialize_property_returns_each_relation_with_one_query(chart):
    amount, units, region = chart["amount"], chart["units"], chart["region"]
    expected = {
        SERIES: [
            [("field_id", amount.id), ("aggregation_type", "sum")],
            [("field_id", units.id), ("aggregation_type", "sum")],
        ],
        GROUP_BYS: [[("field_id", region.id)]],
        SORTS: [
            [
                ("sort_on", "SERIES"),
                ("reference", f"field_{amount.id}_sum"),
                ("direction", "ASC"),
            ],
            [("sort_on", "GROUP_BY"), ("reference", ""), ("direction", "DESC")],
        ],
    }
    service = fresh(chart["service_id"])

    for prop_name, payload in expected.items():
        with CaptureQueriesContext(connection) as context:
            value = service_type().serialize_property(service, prop_name)
        assert ordered(value) == payload
        # Each property reads its own relation and nothing else.
        assert len(context.captured_queries) == 1

    prefetched = service_type().enhance_queryset(
        LocalJadawelGroupedAggregateRows.objects.filter(id=chart["service_id"])
    )[0]
    with CaptureQueriesContext(connection) as context:
        values = [
            service_type().serialize_property(prefetched, name) for name in expected
        ]
    assert [ordered(v) for v in values] == list(expected.values())
    assert len(context.captured_queries) == 0

    assert service_type().serialize_property(service, "table_id") == chart["table"].id
    assert service_type().serialize_property(service, "type") == (
        "local_jadawel_grouped_aggregate_rows"
    )


@pytest.mark.django_db
def test_export_prepared_values_ends_with_the_three_relations(chart):
    amount, units, region = chart["amount"], chart["units"], chart["region"]

    values = service_type().export_prepared_values(fresh(chart["service_id"]))

    assert list(values)[-3:] == [SERIES, GROUP_BYS, SORTS]
    assert ordered(values[SERIES]) == [
        [("field_id", amount.id), ("aggregation_type", "sum")],
        [("field_id", units.id), ("aggregation_type", "sum")],
    ]
    assert ordered(values[GROUP_BYS]) == [[("field_id", region.id)]]
    assert ordered(values[SORTS]) == [
        [
            ("sort_on", "SERIES"),
            ("reference", f"field_{amount.id}_sum"),
            ("direction", "ASC"),
        ],
        [("sort_on", "GROUP_BY"), ("reference", ""), ("direction", "DESC")],
    ]
    assert values["table_id"] == chart["table"].id


# --- c. prepare_values defaults ----------------------------------------------


@pytest.mark.django_db
def test_a_sort_without_a_direction_is_stored_ascending(chart):
    # The serializer and the model both default to DESC, but prepare_values
    # fills a missing direction with ASC. That quirk is pinned here.
    configure(
        chart,
        service_aggregation_sorts=[
            {"sort_on": SORT_ON_SERIES, "reference": f"field_{chart['units'].id}_sum"},
            {},
            {"sort_on": SORT_ON_GROUP_BY, "reference": None, "direction": "DESC"},
        ],
    )

    assert rows_of(fresh(chart["service_id"]))["sorts"] == [
        ("SERIES", f"field_{chart['units'].id}_sum", "ASC", 0),
        ("SERIES", "", "ASC", 1),
        ("GROUP_BY", "", "DESC", 2),
    ]
    field = LocalJadawelTableServiceAggregationSortBy._meta.get_field("direction")
    assert field.default == "DESC"


@pytest.mark.django_db
def test_null_relations_clear_them(chart):
    configure(
        chart,
        service_aggregation_series=None,
        service_aggregation_group_bys=None,
        service_aggregation_sorts=None,
    )

    assert rows_of(fresh(chart["service_id"])) == {
        "series": [],
        "group_bys": [],
        "sorts": [],
    }


# --- validation ---------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("prop_name", [SERIES, GROUP_BYS])
def test_a_field_of_another_table_is_an_invalid_field(chart, prop_name):
    other_amount = chart["other_amount"]
    entry = {"field_id": other_amount.id}
    if prop_name == SERIES:
        entry["aggregation_type"] = "sum"

    with pytest.raises(DRFValidationError) as error:
        configure(chart, **{prop_name: [entry]})

    assert error.value.get_codes() == ["invalid_field"]
    assert [str(d) for d in error.value.detail] == [
        f"The field with ID {other_amount.id} is not related to the given table."
    ]
    assert len(rows_of(fresh(chart["service_id"]))["series"]) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("prop_name", [SERIES, GROUP_BYS])
def test_a_field_without_a_table_is_an_invalid_field(chart, prop_name):
    widget = WidgetService().create_widget(
        chart["user"], "chart", chart["dashboard"].id, title="New", description=""
    )
    entry = {"field_id": chart["amount"].id}
    if prop_name == SERIES:
        entry["aggregation_type"] = "sum"

    with pytest.raises(DRFValidationError) as error:
        configure(chart, widget=widget, **{prop_name: [entry]})

    assert error.value.get_codes() == ["invalid_field"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,aggregation_type,code",
    [
        # The aggregation type is checked first, then the field's table, then
        # whether the aggregation exists and fits the field.
        ("other_amount", "distribution", "unsupported_aggregation_type"),
        ("other_amount", "not_registered", "invalid_field"),
        ("amount", "not_registered", "invalid_aggregation_raw_type"),
        ("region", "sum", "invalid_aggregation_raw_type"),
    ],
)
def test_series_validation_order(chart, field, aggregation_type, code):
    with pytest.raises(DRFValidationError) as error:
        configure(
            chart,
            service_aggregation_series=[
                {"field_id": chart[field].id, "aggregation_type": aggregation_type}
            ],
        )

    assert error.value.get_codes() == [code]


# --- d. after_update ---------------------------------------------------------


def update(setup, **values):
    """
    Runs the update the data source handler runs, after prepare_values, and
    returns the handler result with the captured statements.
    """

    service = fresh(setup["service_id"])
    prepared = service_type().prepare_values(values, setup["user"], service)
    with CaptureQueriesContext(connection) as context:
        updated = ServiceHandler().update_service(service_type(), service, **prepared)
    return updated, context


@pytest.mark.django_db
def test_an_update_without_a_table_change_rewrites_only_the_given_relations(chart):
    amount, units, region = chart["amount"], chart["units"], chart["region"]
    new_series = [{"field_id": units.id, "aggregation_type": "sum"}]
    new_sorts = [{"sort_on": SORT_ON_GROUP_BY, "reference": "", "direction": "ASC"}]
    # Warm every process-level cache with the same update first.
    update(chart, service_aggregation_series=new_series, service_aggregation_sorts=[])

    updated, context = update(
        chart,
        service_aggregation_series=new_series,
        service_aggregation_sorts=new_sorts,
    )

    assert rows_of(fresh(chart["service_id"])) == {
        "series": [(units.id, "sum", 0)],
        "group_bys": [(region.id, 0)],
        "sorts": [("GROUP_BY", "", "ASC", 0)],
    }
    assert statements(context) == [
        # export_prepared_values before the update
        ("SELECT", INTEGRATION_TABLE),
        *EXPORT_PREPARED_VALUES,
        *SAVE_SERVICE,
        # the series, then the sorts, each deleted and recreated; the group bys
        # are not in the values and are left alone
        ("SELECT", SERIES_TABLE),
        ("DELETE", SERIES_TABLE),
        ("INSERT", SERIES_TABLE),
        ("SELECT", SORT_TABLE),
        ("INSERT", SORT_TABLE),
        # export_prepared_values after the update
        *EXPORT_PREPARED_VALUES,
    ]
    original, new = updated.original_service_values, updated.new_service_values
    assert original[SERIES] == [{"field_id": units.id, "aggregation_type": "sum"}]
    assert original[SORTS] == []
    assert new[SERIES] == [{"field_id": units.id, "aggregation_type": "sum"}]
    assert new[GROUP_BYS] == [{"field_id": region.id}]
    assert new[SORTS] == [{"sort_on": "GROUP_BY", "reference": "", "direction": "ASC"}]
    assert amount.id not in [s["field_id"] for s in new[SERIES]]


@pytest.mark.django_db
def test_a_table_change_drops_the_relations_then_writes_the_new_ones(chart):
    amount = chart["amount"]
    other_amount = chart["other_amount"]
    # Moving the chart away first warms the caches with a table change.
    update(
        chart,
        table_id=chart["other_table"].id,
        service_aggregation_series=[
            {"field_id": other_amount.id, "aggregation_type": "sum"}
        ],
    )
    assert rows_of(fresh(chart["service_id"])) == {
        "series": [(other_amount.id, "sum", 0)],
        "group_bys": [],
        "sorts": [],
    }
    configure(
        chart,
        service_aggregation_group_bys=[{"field_id": chart["other_region"].id}],
        service_aggregation_sorts=[{"sort_on": SORT_ON_GROUP_BY}],
    )

    updated, context = update(
        chart,
        table_id=chart["table"].id,
        service_aggregation_series=[{"field_id": amount.id, "aggregation_type": "max"}],
    )

    # The series sent with the table describe the new table and are kept.
    assert rows_of(fresh(chart["service_id"])) == {
        "series": [(amount.id, "max", 0)],
        "group_bys": [],
        "sorts": [],
    }
    assert statements(context) == [
        ("SELECT", INTEGRATION_TABLE),
        *EXPORT_PREPARED_VALUES,
        *SAVE_SERVICE,
        # the core service drops its filters on a table change
        ("SELECT", FILTER_TABLE),
        # then all three relations go, in this order
        ("SELECT", SERIES_TABLE),
        ("DELETE", SERIES_TABLE),
        ("SELECT", GROUP_BY_TABLE),
        ("DELETE", GROUP_BY_TABLE),
        ("SELECT", SORT_TABLE),
        ("DELETE", SORT_TABLE),
        # then the series given with the update are written
        ("SELECT", SERIES_TABLE),
        ("INSERT", SERIES_TABLE),
        *EXPORT_PREPARED_VALUES,
    ]
    assert updated.original_service_values[GROUP_BYS] == [
        {"field_id": chart["other_region"].id}
    ]
    assert updated.new_service_values[GROUP_BYS] == []
    assert updated.new_service_values["table_id"] == chart["table"].id


@pytest.mark.django_db
def test_a_table_change_with_no_relations_in_the_values_only_drops_them(chart):
    update(chart, table_id=chart["other_table"].id)

    updated, context = update(chart, table_id=chart["table"].id)

    assert rows_of(fresh(chart["service_id"])) == {
        "series": [],
        "group_bys": [],
        "sorts": [],
    }
    # The relations are already empty, so each delete only reads.
    assert statements(context) == [
        ("SELECT", INTEGRATION_TABLE),
        *EXPORT_PREPARED_VALUES,
        *SAVE_SERVICE,
        ("SELECT", FILTER_TABLE),
        ("SELECT", SERIES_TABLE),
        ("SELECT", GROUP_BY_TABLE),
        ("SELECT", SORT_TABLE),
        *EXPORT_PREPARED_VALUES,
    ]
    assert updated.new_service_values[SERIES] == []


# --- e. import ------------------------------------------------------------------


@pytest.mark.django_db
def test_an_import_creates_the_relations_without_deleting_anything(chart):
    exported = json.loads(
        json.dumps(ServiceHandler().export_service(fresh(chart["service_id"])))
    )
    integration = fresh(chart["service_id"]).integration
    id_mapping = {
        "database_tables": {chart["table"].id: chart["other_table"].id},
        "database_fields": {
            chart["amount"].id: chart["other_amount"].id,
            chart["units"].id: chart["other_units"].id,
            chart["region"].id: chart["other_region"].id,
        },
    }
    # Warm every process-level cache with the same import first.
    ServiceHandler().import_service(
        integration, copy.deepcopy(exported), copy.deepcopy(id_mapping)
    )

    with CaptureQueriesContext(connection) as context:
        imported = ServiceHandler().import_service(
            integration, copy.deepcopy(exported), copy.deepcopy(id_mapping)
        )

    other_amount_id = chart["other_amount"].id
    assert imported.table_id == chart["other_table"].id
    assert rows_of(fresh(imported.id)) == {
        "series": [
            (other_amount_id, "sum", 0),
            (chart["other_units"].id, "sum", 1),
        ],
        "group_bys": [(chart["other_region"].id, 0)],
        "sorts": [
            ("SERIES", f"field_{other_amount_id}_sum", "ASC", 0),
            ("GROUP_BY", "", "DESC", 1),
        ],
    }
    # No DELETE and no read: the three relations are only created.
    assert statements(context) == [
        ("INSERT", SERVICE_TABLE),
        ("INSERT", GROUPED_TABLE),
        ("INSERT", SERIES_TABLE),
        ("INSERT", GROUP_BY_TABLE),
        ("INSERT", SORT_TABLE),
    ]


@pytest.mark.django_db
def test_an_import_with_empty_relations_inserts_nothing(chart):
    exported = json.loads(
        json.dumps(ServiceHandler().export_service(fresh(chart["service_id"])))
    )
    exported[SERIES] = []
    exported[GROUP_BYS] = []
    del exported[SORTS]
    integration = fresh(chart["service_id"]).integration

    with CaptureQueriesContext(connection) as context:
        imported = ServiceHandler().import_service(integration, exported, {})

    # An empty relation list sends no INSERT at all.
    assert statements(context) == [
        ("INSERT", SERVICE_TABLE),
        ("INSERT", GROUPED_TABLE),
    ]
    assert rows_of(fresh(imported.id)) == {"series": [], "group_bys": [], "sorts": []}


@pytest.mark.django_db
def test_an_imported_sort_without_a_direction_takes_the_model_default(chart):
    exported = json.loads(
        json.dumps(ServiceHandler().export_service(fresh(chart["service_id"])))
    )
    exported[SORTS] = [{"sort_on": SORT_ON_GROUP_BY, "reference": ""}]
    integration = fresh(chart["service_id"]).integration

    imported = ServiceHandler().import_service(integration, exported, {})

    # Unlike prepare_values, the import does not default the direction to ASC.
    assert rows_of(fresh(imported.id))["sorts"] == [("GROUP_BY", "", "DESC", 0)]


# --- f. dispatch with sorts ---------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sorts,groups",
    [
        # No sort: the first series (units) descending.
        ([], ["Jeddah", "Riyadh", "Dammam"]),
        ([("SERIES", "units", "ASC")], ["Dammam", "Riyadh", "Jeddah"]),
        (
            [("SERIES", "amount", "ASC"), ("GROUP_BY", "", "DESC")],
            ["Jeddah", "Dammam", "Riyadh"],
        ),
        (
            [("SERIES", "amount", "ASC"), ("GROUP_BY", "", "ASC")],
            ["Dammam", "Jeddah", "Riyadh"],
        ),
        ([("GROUP_BY", "", "ASC")], ["Dammam", "Jeddah", "Riyadh"]),
        ([("GROUP_BY", "field_1_sum", "DESC")], ["Riyadh", "Jeddah", "Dammam"]),
        # A sort on a series that no longer exists is skipped.
        ([("SERIES", "stale", "ASC")], ["Jeddah", "Riyadh", "Dammam"]),
        (
            [("SERIES", "stale", "ASC"), ("GROUP_BY", "", "ASC")],
            ["Dammam", "Jeddah", "Riyadh"],
        ),
    ],
)
def test_dispatch_orders_the_buckets_by_the_sorts(chart, sorts, groups):
    units, amount = chart["units"], chart["amount"]
    references = {
        "units": f"field_{units.id}_sum",
        "amount": f"field_{amount.id}_sum",
        "stale": "field_999999_sum",
    }
    configure(
        chart,
        service_aggregation_series=[
            {"field_id": units.id, "aggregation_type": "sum"},
            {"field_id": amount.id, "aggregation_type": "sum"},
        ],
        service_aggregation_sorts=[
            {
                "sort_on": sort_on,
                "reference": references.get(reference, reference),
                "direction": direction,
            }
            for sort_on, reference, direction in sorts
        ],
    )

    result = dispatch(chart)

    totals = {"Riyadh": ("3", "30"), "Jeddah": ("4", "5"), "Dammam": ("1", "5")}
    assert result["groups"] == [{"value": g, "color": None} for g in groups]
    assert [s["key"] for s in result["series"]] == [
        f"field_{units.id}_sum",
        f"field_{amount.id}_sum",
    ]
    assert result["series"][0]["data"] == [totals[g][0] for g in groups]
    assert result["series"][1]["data"] == [totals[g][1] for g in groups]
    assert [s["label"] for s in result["series"]] == ["Units", "Amount"]
    assert result["truncated"] is False


@pytest.mark.django_db
def test_dispatch_reports_an_unregistered_aggregation_type(chart):
    LocalJadawelTableServiceAggregationSeries.objects.filter(
        service_id=chart["service_id"], field_id=chart["units"].id
    ).update(aggregation_type="not_registered")

    with pytest.raises(ServiceImproperlyConfiguredDispatchException) as error:
        dispatch(chart)

    assert str(error.value) == (
        "The field_aggregations type not_registered does not exist."
    )


# --- widget serializer overrides ----------------------------------------------


DATA_SOURCE_ID_HELP = "References a data source field for the widget."


@pytest.mark.django_db
@pytest.mark.parametrize(
    "widget_type,field_ids_help",
    [
        (ChartWidgetType, None),
        (ProgressWidgetType, None),
        (
            RecordsListWidgetType,
            "Ids of the fields to show, in order. An empty list lets the widget "
            "choose.",
        ),
        (
            UpcomingDatesWidgetType,
            "Ids of the fields to show alongside the date, in order.",
        ),
    ],
)
def test_widget_serializer_overrides(widget_type, field_ids_help):
    instance = widget_type()

    assert instance.request_serializer_field_overrides == {}
    assert instance.get_field_overrides(True, {}) == {}

    overrides = instance.serializer_field_overrides
    expected_keys = ["data_source_id"] + (["field_ids"] if field_ids_help else [])
    assert list(overrides) == expected_keys
    assert list(instance.get_field_overrides(False, {})) == expected_keys

    data_source_id = overrides["data_source_id"]
    assert isinstance(data_source_id, serializers.PrimaryKeyRelatedField)
    assert data_source_id.required is False
    assert data_source_id.default is None
    assert data_source_id.help_text == DATA_SOURCE_ID_HELP
    assert data_source_id.queryset.model is DashboardDataSource

    fields = instance.get_serializer_class()().fields
    assert fields["data_source_id"].help_text == DATA_SOURCE_ID_HELP
    if field_ids_help:
        field_ids = overrides["field_ids"]
        assert type(field_ids) is serializers.ListField
        assert type(field_ids.child) is serializers.IntegerField
        assert field_ids.required is False
        assert field_ids.max_length == 6
        assert field_ids.help_text == field_ids_help
        assert fields["field_ids"].help_text == field_ids_help
        # A fresh field each time, as a serializer field cannot be shared.
        assert instance.serializer_field_overrides["field_ids"] is not field_ids
