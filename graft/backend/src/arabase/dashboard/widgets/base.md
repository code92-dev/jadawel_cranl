# backend/src/arabase/dashboard/widgets/base.py

- DataSourceBackedWidgetType · class · L13-L93 — class DataSourceBackedWidgetType(WidgetType)
- SerializedDict · class · L26-L27 — class SerializedDict(WidgetDict)
- data_source_serializer_field_overrides · method · L30-L38 — def data_source_serializer_field_overrides(self)
- prepare_value_for_db · method · L40-L51 — def prepare_value_for_db(self, values: dict, instance: Widget | None = None)
- before_trashed · method · L53-L55 — def before_trashed(self, instance: Widget)
- before_restore · method · L57-L59 — def before_restore(self, instance: Widget)
- after_delete · method · L61-L62 — def after_delete(self, instance: Widget)
- deserialize_property · method · L64-L74 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: dict[str, Any], **kwargs, ) -> Any
- serialize_property · method · L76-L93 — def serialize_property( self, instance: Widget, prop_name: str, files_zip=None, storage=None, cache=None, )
- DisplayedFieldsWidgetTypeMixin · class · L96-L131 — class DisplayedFieldsWidgetTypeMixin
- deserialize_property · method · L116-L131 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: dict[str, Any], **kwargs, ) -> Any
