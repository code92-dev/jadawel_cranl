# backend/src/arabase/kanban/view_types.py

- KanbanViewFieldOptionsSerializer · class · L37-L40 — class KanbanViewFieldOptionsSerializer(serializers.ModelSerializer)
- Meta · class · L38-L40 — class Meta
- KanbanViewType · class · L43-L335 — class KanbanViewType(ViewType)
- get_api_urls · method · L86-L91 — def get_api_urls(self)
- prepare_values · method · L93-L126 — def prepare_values(self, values, table, user)
- export_prepared_values · method · L128-L141 — def export_prepared_values(self, view: KanbanView) -> Dict[str, Any]
- after_field_delete · method · L143-L157 — def after_field_delete(self, field)
- after_fields_type_change · method · L159-L196 — def after_fields_type_change(self, fields)
- view_created · method · L198-L209 — def view_created(self, view)
- get_visible_field_options_in_order · method · L211-L220 — def get_visible_field_options_in_order(self, kanban_view: KanbanView) -> QuerySet
- get_hidden_fields · method · L222-L250 — def get_hidden_fields( self, view: KanbanView, field_ids_to_check=None, )
- enhance_queryset · method · L252-L253 — def enhance_queryset(self, queryset)
- export_serialized · method · L255-L283 — def export_serialized( self, kanban: View, import_export_config: ImportExportConfig, cache: Dict, files_zip: Optional[ExportZipFile] = None, storage=None, )
- import_serialized · method · L285-L335 — def import_serialized( self, table, serialized_values: Dict[str, Any], import_export_config: ImportExportConfig, id_mapping: Dict[str, Any], cache: Dict, files_zip: Optional[ZipFile] = None, storage=None, ) -> Optional[View]
