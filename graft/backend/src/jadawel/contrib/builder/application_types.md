# backend/src/jadawel/contrib/builder/application_types.py

- lazy_get_instance_serializer_class · function · L46-L49 — def lazy_get_instance_serializer_class()
- lazy_get_instance_public_serializer_class · function · L52-L55 — def lazy_get_instance_public_serializer_class()
- BuilderApplicationType · class · L58-L601 — class BuilderApplicationType(ApplicationType)
- serializer_field_overrides · method · L92-L114 — def serializer_field_overrides(self)
- get_api_urls · method · L116-L121 — def get_api_urls(self)
- export_safe_transaction_context · method · L123-L124 — def export_safe_transaction_context(self, application: Application) -> Atomic
- init_application · method · L126-L171 — def init_application(self, user: AbstractUser, application: Application) -> None
- export_serialized · method · L173-L264 — def export_serialized( self, builder: Builder, import_export_config: ImportExportConfig, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> BuilderDict
- import_integrations_serialized · method · L266-L307 — def import_integrations_serialized( self, builder: Builder, serialized_integrations: List[Dict[str, Any]], id_mapping: Dict[str, Any], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> List[Integration]
- import_user_sources_serialized · method · L309-L367 — def import_user_sources_serialized( self, builder: Builder, serialized_user_sources: List[Dict[str, Any]], id_mapping: Dict[str, Any], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> List[Page]
- import_serialized · method · L369-L478 — def import_serialized( self, workspace: Workspace, serialized_values: Dict[str, Any], import_export_config: ImportExportConfig, id_mapping: Dict[str, Any], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> Application
- get_application_urls · method · L480-L502 — def get_application_urls(self, application: Builder) -> list[str]
- _extract_builder_id_from_path · method · L505-L515 — def _extract_builder_id_from_path(cls, url_path): # Define the regex pattern with a capturing group for the integer
- get_application_id_for_url · method · L518-L547 — def get_application_id_for_url(cls, url: str) -> int | None
- _get_base_enhanced_queryset · method · L549-L553 — def _get_base_enhanced_queryset(self, queryset)
- enhance_queryset · method · L555-L557 — def enhance_queryset(self, queryset)
- enhance_and_filter_queryset · method · L559-L577 — def enhance_and_filter_queryset( self, queryset: QuerySet[Builder], user: AbstractUser, workspace: Workspace, ) -> QuerySet[Builder]
- fetch_pages_to_serialize · method · L579-L601 — def fetch_pages_to_serialize( self, builder: Builder, user: AbstractUser | None ) -> List[Page]
