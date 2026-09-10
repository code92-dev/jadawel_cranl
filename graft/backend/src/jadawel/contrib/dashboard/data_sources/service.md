# backend/src/jadawel/contrib/dashboard/data_sources/service.py

- DashboardDataSourceService · class · L38-L291 — class DashboardDataSourceService
- __init__ · method · L39-L41 — def __init__(self)
- get_data_source · method · L43-L70 — def get_data_source( self, user: AbstractUser, data_source_id: int ) -> DashboardDataSource
- get_data_sources · method · L72-L105 — def get_data_sources( self, user: AbstractUser, dashboard_id: int ) -> Iterable[DashboardDataSource]
- create_data_source · method · L107-L160 — def create_data_source( self, user: AbstractUser, dashboard_id: int, service_type: ServiceType, name: str | None = None, **kwargs, ) -> DashboardDataSource
- update_data_source · method · L162-L221 — def update_data_source( self, user: AbstractUser, data_source_id: int, service_type: ServiceType, **kwargs, ) -> UpdatedDashboardDataSource
- delete_data_source · method · L223-L252 — def delete_data_source(self, user: AbstractUser, data_source_id: int)
- dispatch_data_source · method · L254-L291 — def dispatch_data_source( self, user, data_source_id: int, dispatch_context: DashboardDispatchContext, ) -> Any
