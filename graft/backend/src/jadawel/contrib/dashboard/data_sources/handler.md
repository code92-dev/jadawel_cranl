# backend/src/jadawel/contrib/dashboard/data_sources/handler.py

- DashboardDataSourceHandler · class · L31-L401 — class DashboardDataSourceHandler
- __init__ · method · L32-L33 — def __init__(self)
- get_data_source · method · L35-L60 — def get_data_source( self, data_source_id: int, base_queryset: QuerySet | None = None ) -> DashboardDataSource
- get_data_source_for_update · method · L62-L88 — def get_data_source_for_update( self, data_source_id: int, base_queryset=None ) -> DashboardDataSourceForUpdate
- get_data_sources · method · L90-L149 — def get_data_sources( self, dashboard: Dashboard, base_queryset: QuerySet | None = None, return_specific_services: bool = True, ) -> Iterable[DashboardDataSource]
- find_unused_data_source_name · method · L151-L167 — def find_unused_data_source_name( self, dashboard: Dashboard, proposed_name: str ) -> str
- create_data_source · method · L169-L197 — def create_data_source( self, dashboard: Dashboard, name: str, service_type: ServiceType, **kwargs, ) -> DashboardDataSource
- update_data_source · method · L199-L265 — def update_data_source( self, data_source: DashboardDataSourceForUpdate, service_type: ServiceType, name: str | None = None, **kwargs, ) -> UpdatedDashboardDataSource
- delete_data_source · method · L267-L280 — def delete_data_source(self, data_source: DashboardDataSource)
- dispatch_data_source · method · L282-L311 — def dispatch_data_source( self, data_source: DashboardDataSource, dispatch_context: DashboardDispatchContext, ) -> Any
- export_data_source · method · L313-L342 — def export_data_source( self, data_source: DashboardDataSource, files_zip: ExportZipFile | None = None, storage: Storage | None = None, cache: dict[str, any] | None = None, ) -> DashboardDataSourceDict
- import_data_source · method · L344-L401 — def import_data_source( self, dashboard: Dashboard, serialized_data_source: DashboardDataSourceDict, id_mapping: dict[str, dict[int, int]], files_zip: ExportZipFile | None = None, storage: Storage | None = None, cache: dict[str, any] | None = None, ) -> DashboardDataSource
