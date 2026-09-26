import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import FieldDoesNotExist as DjangoFieldDoesNotExist
from django.db.models import Count, F
from django.db.models.functions import TruncDate

from rest_framework.exceptions import ValidationError as DRFValidationError

from arabase.integrations.local_jadawel.date_columns import (
    field_tzinfo,
    is_datetime_column,
)
from arabase.integrations.local_jadawel.models import (
    SORT_ON_GROUP_BY,
    SORT_ON_SERIES,
    LocalJadawelGroupedAggregateRows,
    LocalJadawelTableServiceAggregationGroupBy,
    LocalJadawelTableServiceAggregationSeries,
    LocalJadawelTableServiceAggregationSortBy,
    remap_series_key,
    series_key,
)
from jadawel.contrib.database.fields.exceptions import IncompatibleField
from jadawel.contrib.database.fields.handler import FieldHandler
from jadawel.contrib.database.fields.registries import (
    field_aggregation_registry,
    field_type_registry,
)
from jadawel.contrib.database.views.exceptions import AggregationTypeDoesNotExist
from jadawel.contrib.database.views.models import SORT_ORDER_ASC
from jadawel.contrib.database.views.view_aggregations import (
    DistributionViewAggregationType,
)
from jadawel.contrib.integrations.local_jadawel.mixins import (
    LocalJadawelTableServiceFilterableMixin,
    LocalJadawelTableServiceSearchableMixin,
)
from jadawel.contrib.integrations.local_jadawel.service_types import (
    LocalJadawelViewServiceType,
)
from jadawel.core.services.dispatch_context import DispatchContext
from jadawel.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)
from jadawel.core.services.registries import DispatchTypes
from jadawel.core.services.types import DispatchResult, ServiceSubClass

logger = logging.getLogger(__name__)

MAX_AGGREGATION_SERIES = 5
"""How many series the API accepts on one service. The frontend offers fewer;
this is the hard stop that keeps a hand-written request from asking the database
for an unbounded number of annotations in a single query."""

_RELATIONS = {
    "service_aggregation_series": (
        LocalJadawelTableServiceAggregationSeries,
        ("field_id", "aggregation_type"),
    ),
    "service_aggregation_group_bys": (
        LocalJadawelTableServiceAggregationGroupBy,
        ("field_id",),
    ),
    "service_aggregation_sorts": (
        LocalJadawelTableServiceAggregationSortBy,
        ("sort_on", "reference", "direction"),
    ),
}
"""
The series, group bys and sorts, in the order they are written and exported.
Each key names the values entry and the service's related manager; it maps to
the relation's model and the fields one exported entry holds, in order.
"""


def _relation_payload(service, key: str) -> List[Dict]:
    """One relation of the service as its exported list of plain dicts."""

    _, fields = _RELATIONS[key]
    return [
        {name: getattr(entry, name) for name in fields}
        for entry in getattr(service, key).all()
    ]


def _bulk_create_relation(service, key: str, entries: List[Dict]) -> None:
    """Creates one relation's entries, numbered in the order they are given."""

    model, _ = _RELATIONS[key]
    model.objects.bulk_create(
        [
            model(service=service, order=index, **entry)
            for index, entry in enumerate(entries)
        ]
    )


def _field_of_table(field_id: int, table):
    """Returns the field, which has to belong to `table`."""

    field = FieldHandler().get_field(field_id)
    if table is None or field.table_id != table.id:
        raise DRFValidationError(
            detail=f"The field with ID {field_id} is not related to the given table.",
            code="invalid_field",
        )
    return field


class LocalJadawelGroupedAggregateRowsUserServiceType(
    LocalJadawelTableServiceSearchableMixin,
    LocalJadawelTableServiceFilterableMixin,
    LocalJadawelViewServiceType,
):
    """
    Aggregations over a Jadawel table or view, bucketed by a field.

    The type name matches upstream Jadawel's premium service so that dashboards
    exported from (or templates shipped by) upstream import into this fork
    instead of being skipped.
    """

    type = "local_jadawel_grouped_aggregate_rows"
    model_class = LocalJadawelGroupedAggregateRows
    dispatch_types = [DispatchTypes.DATA]
    serializer_mixins = LocalJadawelTableServiceFilterableMixin.mixin_serializer_mixins
    returns_list = False

    # Distribution needs a second grouping level to mean anything, and the core
    # aggregate rows service excludes it for the same reason.
    unsupported_aggregation_types = [DistributionViewAggregationType.type]

    def get_schema_name(self, service: LocalJadawelGroupedAggregateRows) -> str:
        return f"GroupedAggregation{service.id}Schema"

    @property
    def simple_formula_fields(self):
        return (
            super().simple_formula_fields
            + LocalJadawelTableServiceSearchableMixin.mixin_simple_formula_fields
        )

    @property
    def allowed_fields(self):
        return (
            super().allowed_fields
            + LocalJadawelTableServiceFilterableMixin.mixin_allowed_fields
            + LocalJadawelTableServiceSearchableMixin.mixin_allowed_fields
        )

    @property
    def serializer_field_names(self):
        return (
            super().serializer_field_names
            + LocalJadawelTableServiceFilterableMixin.mixin_serializer_field_names
            + LocalJadawelTableServiceSearchableMixin.mixin_serializer_field_names
        ) + [
            "aggregation_series",
            "aggregation_group_bys",
            "aggregation_sorts",
        ]

    @property
    def serializer_field_overrides(self):
        from arabase.integrations.local_jadawel.api.serializers import (
            LocalJadawelTableServiceAggregationGroupBySerializer,
            LocalJadawelTableServiceAggregationSeriesSerializer,
            LocalJadawelTableServiceAggregationSortBySerializer,
        )

        return {
            **super().serializer_field_overrides,
            **LocalJadawelTableServiceFilterableMixin.mixin_serializer_field_overrides,
            **LocalJadawelTableServiceSearchableMixin.mixin_serializer_field_overrides,
            "aggregation_series": LocalJadawelTableServiceAggregationSeriesSerializer(
                many=True, source="service_aggregation_series", required=False
            ),
            "aggregation_group_bys": (
                LocalJadawelTableServiceAggregationGroupBySerializer(
                    many=True, source="service_aggregation_group_bys", required=False
                )
            ),
            "aggregation_sorts": LocalJadawelTableServiceAggregationSortBySerializer(
                many=True, source="service_aggregation_sorts", required=False
            ),
        }

    class SerializedDict(
        LocalJadawelViewServiceType.SerializedDict,
        LocalJadawelTableServiceSearchableMixin.SerializedDict,
        LocalJadawelTableServiceFilterableMixin.SerializedDict,
    ):
        service_aggregation_series: List[Dict]
        service_aggregation_group_bys: List[Dict]
        service_aggregation_sorts: List[Dict]

    def enhance_queryset(self, queryset):
        return (
            super()
            .enhance_queryset(queryset)
            .prefetch_related(
                "service_aggregation_series__field",
                "service_aggregation_group_bys__field",
                "service_aggregation_sorts",
            )
        )

    # --- configuration -----------------------------------------------------

    def _validate_series(
        self,
        aggregation_series: List[Dict],
        table,
    ) -> List[Dict]:
        if len(aggregation_series) > MAX_AGGREGATION_SERIES:
            raise DRFValidationError(
                detail=f"At most {MAX_AGGREGATION_SERIES} series are allowed.",
                code="max_number_of_series_exceeded",
            )

        seen = set()
        validated = []
        for entry in aggregation_series:
            field_id = entry.get("field_id", None)
            aggregation_type = entry.get("aggregation_type", "")

            if aggregation_type in self.unsupported_aggregation_types:
                raise DRFValidationError(
                    detail=f"The {aggregation_type} aggregation type is not "
                    "currently supported.",
                    code="unsupported_aggregation_type",
                )

            field = None
            if field_id is not None:
                field = _field_of_table(field_id, table)

            if aggregation_type and field:
                try:
                    agg_type = field_aggregation_registry.get(aggregation_type)
                except AggregationTypeDoesNotExist as exc:
                    raise DRFValidationError(
                        detail=f"The aggregation type {aggregation_type} "
                        "does not exist.",
                        code="invalid_aggregation_raw_type",
                    ) from exc
                if not agg_type.field_is_compatible(field):
                    raise DRFValidationError(
                        detail=f"The field with ID {field_id} is not compatible "
                        f"with aggregation type {aggregation_type}.",
                        code="invalid_aggregation_raw_type",
                    )

            key = series_key(field_id, aggregation_type)
            if key in seen:
                raise DRFValidationError(
                    detail="The same field and aggregation type combination "
                    "cannot be used twice.",
                    code="duplicate_series",
                )
            seen.add(key)

            validated.append(
                {"field_id": field_id, "aggregation_type": aggregation_type}
            )

        return validated

    def _validate_group_bys(self, group_bys: List[Dict], table) -> List[Dict]:
        # v1 supports a single group by. The relation is a list so that adding a
        # second grouping level later does not need a data migration.
        if len(group_bys) > 1:
            raise DRFValidationError(
                detail="Only one group by is supported.",
                code="max_number_of_group_bys_exceeded",
            )

        validated = []
        for entry in group_bys:
            field_id = entry.get("field_id", None)
            if field_id is not None:
                _field_of_table(field_id, table)
            validated.append({"field_id": field_id})

        return validated

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[ServiceSubClass] = None,
    ) -> Dict[str, Any]:
        values = super().prepare_values(values, user, instance)

        table = values.get("table", getattr(instance, "table", None))

        if "service_aggregation_series" in values:
            values["service_aggregation_series"] = self._validate_series(
                values["service_aggregation_series"] or [], table
            )

        if "service_aggregation_group_bys" in values:
            values["service_aggregation_group_bys"] = self._validate_group_bys(
                values["service_aggregation_group_bys"] or [], table
            )

        if "service_aggregation_sorts" in values:
            values["service_aggregation_sorts"] = [
                {
                    "sort_on": entry.get("sort_on", SORT_ON_SERIES),
                    "reference": entry.get("reference", "") or "",
                    "direction": entry.get("direction", SORT_ORDER_ASC),
                }
                for entry in (values["service_aggregation_sorts"] or [])
            ]

        return values

    def after_create(self, instance: LocalJadawelGroupedAggregateRows, values: Dict):
        super().after_create(instance, values)
        self._write_relations(instance, values)

    def after_update(
        self,
        instance: LocalJadawelGroupedAggregateRows,
        values: Dict,
        changes: Dict[str, tuple],
    ) -> None:
        super().after_update(instance, values, changes)

        # Series, group bys and sorts all point at specific table fields, so a
        # table change drops them the same way it drops filters and sorts on the
        # other local Jadawel services.
        #
        # The test is that the table *changed*, not that both ends are set:
        # clearing the table to null is equally a change, and leaving the series
        # pointing at fields of a table the service no longer reads is how a
        # dispatch ends up referencing a removed column.
        from_table, to_table = changes.get("table", (None, None))
        if from_table != to_table:
            for key in _RELATIONS:
                getattr(instance, key).all().delete()

        # Series supplied in the same request describe the *new* table, so they
        # are written back rather than discarded with the old ones.
        self._write_relations(instance, values)

    def _write_relations(
        self, instance: LocalJadawelGroupedAggregateRows, values: Dict
    ) -> None:
        """
        Replaces the series, group bys and sorts wholesale when they are part of
        the values. They are ordered collections with no stable client-side id,
        so a diff would not buy anything over a rewrite.
        """

        for key in _RELATIONS:
            if key in values:
                getattr(instance, key).all().delete()
                _bulk_create_relation(instance, key, values[key])

    def export_prepared_values(
        self, instance: LocalJadawelGroupedAggregateRows
    ) -> dict:
        values = super().export_prepared_values(instance)
        for key in _RELATIONS:
            values[key] = _relation_payload(instance, key)
        return values

    # --- export / import ---------------------------------------------------

    def serialize_property(
        self,
        service: LocalJadawelGroupedAggregateRows,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
    ):
        if prop_name in _RELATIONS:
            return _relation_payload(service, prop_name)

        return super().serialize_property(
            service, prop_name, files_zip=files_zip, storage=storage, cache=cache
        )

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        field_mapping = id_mapping.get("database_fields", {})

        if prop_name in ("service_aggregation_series", "service_aggregation_group_bys"):
            return [
                {**entry, "field_id": field_mapping.get(entry["field_id"], None)}
                for entry in value or []
            ]

        if prop_name == "service_aggregation_sorts":
            # A series sort's reference is a series key, so the field id in it
            # follows the same remapping as the series themselves.
            sorts = []
            for entry in value or []:
                reference = entry.get("reference", "")
                if entry.get("sort_on") == SORT_ON_SERIES:
                    reference = remap_series_key(reference, field_mapping)
                sorts.append({**entry, "reference": reference})
            return sorts

        return super().deserialize_property(
            prop_name,
            value,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def create_instance_from_serialized(
        self,
        serialized_values,
        id_mapping,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        relations = {key: serialized_values.pop(key, []) for key in _RELATIONS}

        service = super().create_instance_from_serialized(
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

        # A new service has nothing to delete, so the relations are only created.
        for key, entries in relations.items():
            _bulk_create_relation(service, key, entries)

        return service

    # --- schema ------------------------------------------------------------

    def generate_schema(
        self,
        service: LocalJadawelGroupedAggregateRows,
        allowed_fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        series = self._untrashed_series(service)
        if not series:
            return None

        if allowed_fields is not None and "result" not in allowed_fields:
            return {}

        properties = {}
        for s in series:
            try:
                aggregation_type = field_aggregation_registry.get(s.aggregation_type)
            except AggregationTypeDoesNotExist:
                # A schema is generated for every data source whenever the
                # dashboard is listed, so letting this escape would turn one
                # series carrying an unregistered aggregation — imported from a
                # deployment that had a plugin this one does not — into a 500 on
                # every dashboard, not just the widget that cannot render.
                # Dropping it from the schema keeps the rest of the page up;
                # dispatching the series still reports the misconfiguration.
                logger.warning(
                    "Service %s references unknown aggregation type %r; "
                    "leaving it out of the schema.",
                    service.id,
                    s.aggregation_type,
                )
                continue
            properties[s.key] = {
                "title": f"{s.field.name} ({s.aggregation_type})",
                "type": "array",
                "items": {"type": aggregation_type.result_type},
            }

        properties["groups"] = {
            "title": "Groups",
            "type": "array",
            "items": {"type": "object"},
        }

        return {
            "title": self.get_schema_name(service),
            "type": "object",
            "properties": {
                "result": {
                    "title": "Result",
                    "type": "object",
                    "properties": properties,
                }
            },
        }

    def get_context_data(
        self,
        service: LocalJadawelGroupedAggregateRows,
        allowed_fields: Optional[List[str]] = None,
    ) -> dict:
        """
        The frontend needs the fields behind the series and the group by to
        label axes and to colour a pie chart with a single select's own colours.
        """

        if allowed_fields is not None and "result" not in allowed_fields:
            return {}

        from jadawel.contrib.database.api.fields.serializers import FieldSerializer

        def serialize(field):
            return field_type_registry.get_serializer(field, FieldSerializer).data

        context_data = {"series": [], "group_bys": []}

        for s in self._untrashed_series(service):
            context_data["series"].append(
                {
                    "key": s.key,
                    "aggregation_type": s.aggregation_type,
                    "field": serialize(s.field),
                }
            )

        for group_by in self._untrashed_group_bys(service):
            context_data["group_bys"].append({"field": serialize(group_by.field)})

        return context_data

    def get_context_data_schema(
        self, service: LocalJadawelGroupedAggregateRows, **kwargs
    ) -> dict | None:
        return None

    def extract_properties(self, service, path: List[str], **kwargs) -> List[str]:
        if path and path[0] == "result":
            return ["result"]
        return []

    # --- dispatch ----------------------------------------------------------

    @staticmethod
    def _untrashed_series(service) -> List[LocalJadawelTableServiceAggregationSeries]:
        return [
            s
            for s in service.service_aggregation_series.all()
            if s.field_id and not s.field.trashed and s.aggregation_type
        ]

    @staticmethod
    def _untrashed_group_bys(
        service,
    ) -> List[LocalJadawelTableServiceAggregationGroupBy]:
        return [
            g
            for g in service.service_aggregation_group_bys.all()
            if g.field_id and not g.field.trashed
        ]

    def resolve_service_formulas(
        self,
        service: LocalJadawelGroupedAggregateRows,
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        series = self._untrashed_series(service)
        if not series:
            raise ServiceImproperlyConfiguredDispatchException(
                "There are no aggregation series."
            )

        for s in series:
            try:
                field_aggregation_registry.get(s.aggregation_type)
            except AggregationTypeDoesNotExist as exc:
                raise ServiceImproperlyConfiguredDispatchException(exc.args[0]) from exc

        return super().resolve_service_formulas(service, dispatch_context)

    def _annotation_for_series(self, queryset, model, series):
        """
        Returns `(queryset, aggregation, agg_type)` for one series, applying any
        annotations the aggregation needs before it can be computed.
        """

        field = series.field.specific
        model_field = model._meta.get_field(field.db_column)
        agg_type = field_aggregation_registry.get(series.aggregation_type)

        if not agg_type.field_is_compatible(field):
            raise IncompatibleField()

        aggregation = agg_type._get_raw_aggregation(model_field, field)

        # Some aggregations are expressed as an annotation plus an aggregate over
        # it; the annotations have to be on the queryset we end up grouping.
        annotations = getattr(aggregation, "annotations", None)
        if annotations is not None:
            queryset = queryset.annotate(**annotations)
            aggregation = aggregation.aggregation

        return queryset, aggregation, agg_type

    def _group_by_expression(self, queryset, group_by_field):
        """
        Returns `(queryset, alias)` naming the column the buckets come from.

        Grouping a datetime field on its raw value gives one bucket per
        microsecond, so those are truncated to the day. Choosing the
        granularity is a v2 setting.
        """

        db_column = group_by_field.db_column

        # What matters is whether the *column* carries a time, which is not the
        # same question as `date_include_time`. That is a display setting, and
        # `created_on` / `last_modified` store a timestamptz whatever it says —
        # so trusting it left those fields untruncated and grouped a timestamp
        # on its raw value, which is exactly the explosion this guards against.
        if is_datetime_column(queryset.model, group_by_field):
            alias = f"{db_column}_bucket"
            tzinfo = field_tzinfo(group_by_field)
            return (
                queryset.annotate(**{alias: TruncDate(db_column, tzinfo=tzinfo)}),
                alias,
            )

        return queryset, db_column

    def dispatch_data(
        self,
        service: LocalJadawelGroupedAggregateRows,
        resolved_values: Dict[str, Any],
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        table = service.table
        series = self._untrashed_series(service)
        group_bys = self._untrashed_group_bys(service)

        try:
            model = self.get_table_model(service)
            queryset = self.build_queryset(
                service, table, dispatch_context, model=model
            )

            aggregations = {}
            needs_total = {}
            agg_types = {}
            for s in series:
                queryset, aggregation, agg_type = self._annotation_for_series(
                    queryset, model, s
                )
                aggregations[s.key] = aggregation
                agg_types[s.key] = agg_type
                if agg_type.with_total:
                    needs_total[s.key] = True

            if needs_total:
                aggregations["total"] = Count("id", distinct=True)

            group_alias = None
            if group_bys:
                queryset, group_alias = self._group_by_expression(
                    queryset, group_bys[0].field
                )
                # `.values()` before `.annotate()` is what turns the aggregate
                # into a GROUP BY rather than a whole-table aggregation.
                rows = queryset.values(group_alias).annotate(**aggregations)
                rows = self._apply_sorts(rows, service, group_alias, series)
                rows = list(rows[: settings.ARABASE_CHART_MAX_BUCKETS + 1])
                truncated = len(rows) > settings.ARABASE_CHART_MAX_BUCKETS
                rows = rows[: settings.ARABASE_CHART_MAX_BUCKETS]
            else:
                rows = [queryset.aggregate(**aggregations)]
                truncated = False
        except DjangoFieldDoesNotExist as exc:
            raise ServiceImproperlyConfiguredDispatchException(
                "One of the aggregated fields does not exist."
            ) from exc
        except IncompatibleField as exc:
            raise ServiceImproperlyConfiguredDispatchException(
                "One of the aggregated fields is not compatible with its "
                "aggregation type."
            ) from exc

        return {
            "data": {
                "rows": rows,
                "truncated": truncated,
                "group_alias": group_alias,
            },
            "jadawel_table_model": model,
            "series": series,
            "group_bys": group_bys,
            "agg_types": agg_types,
            "needs_total": needs_total,
        }

    def _apply_sorts(self, rows, service, group_alias, series):
        """
        Applies the configured sorts, defaulting to the first series descending.

        The default matters: the bucket cap slices the result, so without an
        ordering that puts the interesting buckets first, a table with more
        distinct values than the cap would show an arbitrary subset.
        """

        available_series_keys = {s.key for s in series}
        order_by = []

        for sort in service.service_aggregation_sorts.all():
            if sort.sort_on == SORT_ON_GROUP_BY:
                expression = F(group_alias)
            elif sort.reference in available_series_keys:
                expression = F(sort.reference)
            else:
                # A sort left behind by a removed series is ignored rather than
                # raising: the widget stays usable while it is reconfigured.
                continue
            order_by.append(
                expression.asc(nulls_first=True)
                if sort.direction == SORT_ORDER_ASC
                else expression.desc(nulls_last=True)
            )

        if not order_by and series:
            order_by = [F(series[0].key).desc(nulls_last=True)]

        return rows.order_by(*order_by)

    def dispatch_transform(self, data: Dict[str, Any]) -> DispatchResult:
        """
        Turns the raw grouped rows into the shape the chart widget renders:
        one label list plus one value list per series.
        """

        rows = data["data"]["rows"]
        group_alias = data["data"]["group_alias"]
        series = data["series"]
        group_bys = data["group_bys"]
        agg_types = data["agg_types"]
        needs_total = data["needs_total"]

        label_resolver = (
            self._label_resolver(group_bys[0].field)
            if group_bys
            else (lambda value: None)
        )

        groups = []
        series_values = {s.key: [] for s in series}

        for row in rows:
            if group_alias is not None:
                groups.append(label_resolver(row.get(group_alias)))

            total = row.get("total", None)
            for s in series:
                value = row.get(s.key, None)
                if needs_total.get(s.key):
                    value = agg_types[s.key]._compute_final_aggregation(value, total)
                series_values[s.key].append(self._serialize_value(s, value))

        return DispatchResult(
            data={
                "result": {
                    "groups": groups,
                    "series": [
                        {
                            "key": s.key,
                            "field_id": s.field_id,
                            "aggregation_type": s.aggregation_type,
                            "label": s.field.name,
                            "data": series_values[s.key],
                        }
                        for s in series
                    ],
                    "truncated": data["data"]["truncated"],
                }
            }
        )

    @staticmethod
    def _serialize_value(series, value):
        """
        Aggregations can return values that JSON cannot represent (`Decimal`
        above all), so each one goes back through its field's serializer field
        the same way the ungrouped aggregate service does it.
        """

        if value is None:
            return None
        field = series.field.specific
        return field.get_type().get_serializer_field(field).to_representation(value)

    @staticmethod
    def _label_resolver(group_by_field):
        """
        Returns a callable turning a raw grouped column value into a label the
        chart can print. Single select columns hold an option id, so those are
        resolved to `{"value", "color"}`; everything else is stringified by its
        field type.
        """

        field = group_by_field.specific
        field_type = field_type_registry.get_by_model(field)

        if field_type.can_have_select_options:
            options = {
                option.id: {"value": option.value, "color": option.color}
                for option in field.select_options.all()
            }
            return lambda value: options.get(value, None)

        def resolve(value):
            if value is None:
                return None
            return {"value": str(value), "color": None}

        return resolve
