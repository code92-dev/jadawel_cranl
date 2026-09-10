# backend/src/jadawel/contrib/database/data_sync/models.py

- DataSync · class · L13-L67 — class DataSync( CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin, models.Model, WithRegistry, )
- get_type_registry · method · L60-L67 — def get_type_registry()
- DataSyncSyncedProperty · class · L70-L95 — class DataSyncSyncedProperty(models.Model)
- SyncDataSyncTableJob · class · L98-L105 — class SyncDataSyncTableJob(Job)
- ICalCalendarDataSync · class · L108-L109 — class ICalCalendarDataSync(DataSync)
- PostgreSQLDataSync · class · L112-L131 — class PostgreSQLDataSync(DataSync)
