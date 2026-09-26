from typing import Any

from rest_framework import serializers

from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.data_sources.models import DashboardDataSource
from jadawel.contrib.dashboard.types import WidgetDict
from jadawel.contrib.dashboard.widgets.models import Widget
from jadawel.contrib.dashboard.widgets.registries import WidgetType
from jadawel.core.services.registries import service_type_registry

MAX_DISPLAYED_FIELDS = 6
"""More columns than this stop being readable inside a dashboard widget, whatever
the widget's width."""


class DataSourceBackedWidgetType(WidgetType):
    """
    Shared behaviour for widgets that own exactly one data source.

    Upstream's summary widget spells all of this out inline, which is fine for
    one widget and repetitive for five. A widget's data source is created with it
    (a widget with nowhere to read from is not a usable state to leave a user in),
    follows it into and out of the trash, and is deleted with it.
    """

    service_type_name: str = None
    """The service type the widget's data source is created with."""

    request_serializer_field_overrides = {}

    class SerializedDict(WidgetDict):
        data_source_id: int

    @property
    def data_source_serializer_field_overrides(self):
        return {
            "data_source_id": serializers.PrimaryKeyRelatedField(
                queryset=DashboardDataSource.objects.all(),
                required=False,
                default=None,
                help_text="References a data source field for the widget.",
            )
        }

    @property
    def serializer_field_overrides(self):
        return self.data_source_serializer_field_overrides

    def prepare_value_for_db(self, values: dict, instance: Widget | None = None):
        if instance is None:
            handler = DashboardDataSourceHandler()
            available_name = handler.find_unused_data_source_name(
                values["dashboard"], "WidgetDataSource"
            )
            values["data_source"] = handler.create_data_source(
                dashboard=values["dashboard"],
                name=available_name,
                service_type=service_type_registry.get(self.service_type_name),
            )
        return values

    def before_trashed(self, instance: Widget):
        instance.data_source.trashed = True
        instance.data_source.save()

    def before_restore(self, instance: Widget):
        instance.data_source.trashed = False
        instance.data_source.save()

    def after_delete(self, instance: Widget):
        DashboardDataSourceHandler().delete_data_source(instance.data_source)

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "data_source_id" and value:
            return id_mapping["dashboard_data_sources"][value]

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def serialize_property(
        self,
        instance: Widget,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
    ):
        if prop_name == "data_source_id":
            return instance.data_source_id

        return super().serialize_property(
            instance,
            prop_name,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
        )


class DisplayedFieldsWidgetTypeMixin:
    """
    For widgets that store which fields they show as a list of field ids.

    Field ids are renumbered on import, so a stored list has to be translated or
    the widget would show an arbitrary set of fields — or none. Ids with no
    mapping refer to fields that were never exported (deleted before the export)
    and are dropped.
    """

    default_displayed_field_count: int = 3
    """How many fields the widget falls back to when `field_ids` is empty.

    The frontend resolves the fallback itself, off the data source schema. The
    number is mirrored here because a public dashboard has to decide server-side
    which fields a visitor may read, and the two have to agree or the widget
    renders columns the dispatch refuses to return. Keep it equal to the
    `fallbackCount` the widget component passes to `resolveDisplayedFields`.
    """

    field_ids_help_text: str = ""
    """The OpenAPI help text of the widget's `field_ids`."""

    @property
    def serializer_field_overrides(self):
        return {
            **super().serializer_field_overrides,
            "field_ids": serializers.ListField(
                child=serializers.IntegerField(),
                required=False,
                max_length=MAX_DISPLAYED_FIELDS,
                help_text=self.field_ids_help_text,
            ),
        }

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "field_ids" and value:
            field_mapping = id_mapping.get("database_fields", {})
            return [
                field_mapping[field_id]
                for field_id in value
                if field_id in field_mapping
            ]

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)
