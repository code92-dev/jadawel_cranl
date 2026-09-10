# backend/src/jadawel/contrib/database/table/exceptions.py

- TableDoesNotExist · class · L4-L5 — class TableDoesNotExist(Exception)
- TableNotInDatabase · class · L8-L17 — class TableNotInDatabase(Exception)
- __init__ · method · L11-L17 — def __init__(self, table_id=None, *args, **kwargs)
- InvalidInitialTableData · class · L20-L21 — class InvalidInitialTableData(Exception)
- TableDoesNotBelongToGroup · class · L24-L25 — class TableDoesNotBelongToGroup(Exception)
- InitialSyncTableDataLimitExceeded · class · L28-L32 — class InitialSyncTableDataLimitExceeded(Exception)
- InitialTableDataLimitExceeded · class · L35-L39 — class InitialTableDataLimitExceeded(Exception)
- InitialTableDataDuplicateName · class · L42-L45 — class InitialTableDataDuplicateName(Exception)
- FailedToLockTableDueToConflict · class · L48-L52 — class FailedToLockTableDueToConflict(LockConflict)
