# backend/src/arabase/views/view_types.py

- ContentSecurityPolicyField · class · L22-L37 — class ContentSecurityPolicyField(serializers.Field)
- __init__ · method · L31-L34 — def __init__(self, **kwargs)
- to_representation · method · L36-L37 — def to_representation(self, value)
- HtmlPageViewType · class · L40-L266 — class HtmlPageViewType(ViewType)
- before_public_info · method · L93-L98 — def before_public_info(self, view: HtmlPageView, user) -> None
- handle_view_update · method · L100-L107 — def handle_view_update(self, values: dict, view: HtmlPageView, user)
- get_api_urls · method · L109-L114 — def get_api_urls(self)
- prepare_values · method · L116-L130 — def prepare_values(self, values, table, user)
- export_serialized · method · L132-L163 — def export_serialized( self, html_page: View, import_export_config: ImportExportConfig, cache: Dict, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, )
- import_serialized · method · L165-L202 — def import_serialized( self, table: Table, serialized_values: Dict[str, Any], import_export_config: ImportExportConfig, id_mapping: Dict[str, Any], cache: Dict, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, ) -> Optional[View]
- export_prepared_values · method · L204-L209 — def export_prepared_values(self, view: HtmlPageView) -> Dict[str, Any]
- view_created · method · L211-L228 — def view_created(self, view)
- get_visible_field_options_in_order · method · L230-L235 — def get_visible_field_options_in_order(self, html_page_view: HtmlPageView)
- get_hidden_fields · method · L237-L263 — def get_hidden_fields( self, view: HtmlPageView, field_ids_to_check: Optional[List[int]] = None, ) -> Set[int]
- enhance_queryset · method · L265-L266 — def enhance_queryset(self, queryset)
