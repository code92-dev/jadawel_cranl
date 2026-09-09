# backend/src/jadawel/contrib/builder/data_sources/service.py

- DataSourceService · class · L41-L445 — class DataSourceService
- __init__ · method · L42-L43 — def __init__(self)
- get_data_source · method · L45-L64 — def get_data_source(self, user: AbstractUser, data_source_id: int) -> DataSource
- get_data_sources · method · L66-L96 — def get_data_sources( self, user: AbstractUser, page: Page, with_shared: bool = False ) -> List[DataSource]
- get_builder_data_sources · method · L98-L122 — def get_builder_data_sources( self, user: AbstractUser, builder: "Builder", with_cache=False ) -> List[DataSource]
- create_data_source · method · L124-L198 — def create_data_source( self, user: AbstractUser, page: Page, service_type: ServiceType, name: Optional[str] = None, before: Optional[DataSource] = None, **kwargs, ) -> DataSource
- update_data_source · method · L200-L263 — def update_data_source( self, user: AbstractUser, data_source: DataSourceForUpdate, service_type: Optional[ServiceType] = None, **kwargs, ) -> DataSource
- delete_data_source · method · L265-L287 — def delete_data_source(self, user: AbstractUser, data_source: DataSourceForUpdate)
- dispatch_data_sources · method · L289-L341 — def dispatch_data_sources( self, user, data_sources: List[DataSource], dispatch_context: BuilderDispatchContext, ) -> Dict[int, Union[Any, Exception]]
- dispatch_page_data_sources · method · L343-L370 — def dispatch_page_data_sources( self, user, page: Page, dispatch_context: BuilderDispatchContext, ) -> Dict[int, Union[Any, Exception]]
- dispatch_data_source · method · L372-L394 — def dispatch_data_source( self, user, data_source: DataSource, dispatch_context: BuilderDispatchContext, ) -> Any
- move_data_source · method · L396-L435 — def move_data_source( self, user: AbstractUser, data_source: DataSourceForUpdate, before: Optional[DataSource] = None, ) -> DataSource
- recalculate_full_orders · method · L437-L445 — def recalculate_full_orders(self, user: AbstractUser, page: Page)
