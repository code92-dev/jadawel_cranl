# backend/src/jadawel/contrib/dashboard/application_types.py

- DashboardApplicationType · class · L24-L199 — class DashboardApplicationType(ApplicationType)
- get_api_urls · method · L31-L36 — def get_api_urls(self)
- export_safe_transaction_context · method · L38-L39 — def export_safe_transaction_context(self, application: Application) -> Atomic
- init_application · method · L41-L48 — def init_application(self, user, application: "Application") -> None
- pre_delete · method · L50-L59 — def pre_delete(self, dashboard)
- export_serialized · method · L61-L118 — def export_serialized( self, dashboard: Dashboard, import_export_config: ImportExportConfig, files_zip: ExportZipFile | None = None, storage: Storage | None = None, progress_builder: ChildProgressBuilder | None = None, ) -> DashboardDict
- import_serialized · method · L120-L199 — def import_serialized( self, workspace: Workspace, serialized_values: dict[str, any], import_export_config: ImportExportConfig, id_mapping: dict[str, dict[int, int]], files_zip: ExportZipFile | None = None, storage: Storage | None = None, cache: dict[str, any] | None = None, progress_builder: ChildProgressBuilder | None = None, ) -> Application
