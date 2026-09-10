# backend/src/jadawel/contrib/database/data_sync/handler.py

- DataSyncHandler · class · L47-L715 — class DataSyncHandler
- get_data_sync · method · L48-L74 — def get_data_sync( self, data_sync_id: int, base_queryset: Optional[QuerySet] = None ) -> DataSync
- _get_two_way_sync_strategy_type · method · L76-L82 — def _get_two_way_sync_strategy_type(self, data_sync_type)
- create_data_sync_table · method · L84-L219 — def create_data_sync_table( self, user: AbstractUser, database: Database, type_name: str, synced_properties: List[str], table_name: str, **kwargs: dict, ) -> DataSync
- update_data_sync_table · method · L221-L286 — def update_data_sync_table( self, user: AbstractUser, data_sync: DataSync, synced_properties: List[str], **kwargs: dict, ) -> DataSync
- get_table_sync_lock_key · method · L288-L289 — def get_table_sync_lock_key(self, data_sync_id)
- sync_data_sync_table · method · L291-L353 — def sync_data_sync_table( self, user: AbstractUser, data_sync: DataSync, progress_builder: Optional[ChildProgressBuilder] = None, ) -> DataSync
- _do_sync_table · method · L355-L516 — def _do_sync_table(self, user, data_sync, progress_builder)
- set_data_sync_synced_properties · method · L518-L715 — def set_data_sync_synced_properties( self, user: Optional[AbstractUser], data_sync: DataSync, synced_properties: List[str], data_sync_properties: Optional[List[DataSyncSyncedProperty]] = None, )
