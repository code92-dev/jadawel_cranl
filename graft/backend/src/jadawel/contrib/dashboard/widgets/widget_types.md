# backend/src/jadawel/contrib/dashboard/widgets/widget_types.py

- SummaryWidgetType · class · L18-L98 — class SummaryWidgetType(WidgetType)
- SerializedDict · class · L33-L34 — class SerializedDict(WidgetDict)
- prepare_value_for_db · method · L36-L51 — def prepare_value_for_db(self, values: dict, instance: Widget | None = None)
- before_trashed · method · L53-L55 — def before_trashed(self, instance: Widget)
- before_restore · method · L57-L59 — def before_restore(self, instance: Widget)
- after_delete · method · L61-L62 — def after_delete(self, instance: Widget)
- deserialize_property · method · L64-L79 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: dict[str, Any], **kwargs, ) -> Any
- serialize_property · method · L81-L98 — def serialize_property( self, instance: Widget, prop_name: str, files_zip=None, storage=None, cache=None, )
