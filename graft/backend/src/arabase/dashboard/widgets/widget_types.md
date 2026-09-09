# backend/src/arabase/dashboard/widgets/widget_types.py

- ChartWidgetType · class · L32-L93 — class ChartWidgetType(DataSourceBackedWidgetType)
- SerializedDict · class · L55-L58 — class SerializedDict(DataSourceBackedWidgetType.SerializedDict)
- serializer_field_overrides · method · L61-L62 — def serializer_field_overrides(self)
- deserialize_property · method · L64-L74 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: dict[str, Any], **kwargs, ) -> Any
- _remap_series_config · method · L77-L93 — def _remap_series_config(series_config: dict, id_mapping: dict[str, Any]) -> dict
- RecordsListWidgetType · class · L96-L121 — class RecordsListWidgetType(DisplayedFieldsWidgetTypeMixin, DataSourceBackedWidgetType)
- SerializedDict · class · L107-L108 — class SerializedDict(DataSourceBackedWidgetType.SerializedDict)
- serializer_field_overrides · method · L111-L121 — def serializer_field_overrides(self)
- ProgressWidgetType · class · L124-L188 — class ProgressWidgetType(DataSourceBackedWidgetType)
- SerializedDict · class · L151-L155 — class SerializedDict(DataSourceBackedWidgetType.SerializedDict)
- serializer_field_overrides · method · L158-L159 — def serializer_field_overrides(self)
- prepare_value_for_db · method · L161-L188 — def prepare_value_for_db(self, values: dict, instance=None)
- UpcomingDatesWidgetType · class · L191-L220 — class UpcomingDatesWidgetType( DisplayedFieldsWidgetTypeMixin, DataSourceBackedWidgetType )
- SerializedDict · class · L207-L208 — class SerializedDict(DataSourceBackedWidgetType.SerializedDict)
- serializer_field_overrides · method · L211-L220 — def serializer_field_overrides(self)
