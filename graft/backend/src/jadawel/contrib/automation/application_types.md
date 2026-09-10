# backend/src/jadawel/contrib/automation/application_types.py

- lazy_get_instance_serializer_class · function · L30-L33 — def lazy_get_instance_serializer_class()
- AutomationApplicationType · class · L36-L292 — class AutomationApplicationType(ApplicationType)
- get_api_urls · method · L52-L57 — def get_api_urls(self)
- export_safe_transaction_context · method · L59-L60 — def export_safe_transaction_context(self, application: Automation) -> Atomic
- init_application · method · L62-L74 — def init_application(self, user: AbstractUser, application: Automation) -> None
- export_serialized · method · L76-L129 — def export_serialized( self, automation: Automation, import_export_config: ImportExportConfig, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: ChildProgressBuilder | None = None, workflows: Optional[List[AutomationWorkflow]] = None, ) -> AutomationDict
- import_integrations_serialized · method · L131-L173 — def import_integrations_serialized( self, automation: Automation, serialized_integrations: List[Dict[str, Any]], id_mapping: Dict[str, Any], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> List[Integration]
- import_serialized · method · L175-L242 — def import_serialized( self, workspace: Workspace, serialized_values: Dict[str, Any], import_export_config: ImportExportConfig, id_mapping: Dict[str, Any], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, progress_builder: Optional[ChildProgressBuilder] = None, ) -> Application
- fetch_workflows_to_serialize · method · L244-L264 — def fetch_workflows_to_serialize( self, automation: Application, user: AbstractUser | None ) -> List[AutomationWorkflow]
- _get_workflows_queryset · method · L266-L269 — def _get_workflows_queryset(self) -> QuerySet[AutomationWorkflow]
- enhance_queryset · method · L271-L274 — def enhance_queryset(self, queryset)
- enhance_and_filter_queryset · method · L276-L292 — def enhance_and_filter_queryset( self, queryset: QuerySet[Automation], user: AbstractUser, workspace: Workspace, ) -> QuerySet[Automation]
