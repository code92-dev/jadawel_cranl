# backend/src/jadawel/contrib/dashboard/widgets/registries.py

- WidgetType · class · L25-L163 — class WidgetType( EasyImportExportMixin[Widget], CustomFieldsInstanceMixin, ModelInstanceMixin[Widget], Instance, ABC, )
- enhance_queryset · method · L39-L48 — def enhance_queryset(self, queryset: QuerySet[Widget]) -> QuerySet[Widget]
- before_create · method · L50-L61 — def before_create(self, user, dashboard: Dashboard)
- after_update · method · L63-L72 — def after_update(self, updated_widget: UpdatedWidget, **kwargs) -> UpdatedWidget
- prepare_value_for_db · method · L74-L84 — def prepare_value_for_db(self, values: dict, instance: Widget | None = None)
- export_prepared_values · method · L86-L97 — def export_prepared_values(self, instance: Widget)
- after_delete · method · L99-L107 — def after_delete(self, instance: Widget)
- before_trashed · method · L109-L117 — def before_trashed(self, instance: Widget)
- before_restore · method · L119-L127 — def before_restore(self, instance: Widget)
- deserialize_property · method · L129-L144 — def deserialize_property( self, prop_name: str, value: any, id_mapping: dict[str, any], **kwargs, ) -> any
- serialize_property · method · L146-L163 — def serialize_property( self, instance: Widget, prop_name: str, files_zip=None, storage=None, cache=None, )
- WidgetTypeRegistry · class · L166-L176 — class WidgetTypeRegistry( Registry[WidgetType], ModelRegistryMixin[Widget, WidgetType], CustomFieldsRegistryMixin, )
