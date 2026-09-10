# backend/src/jadawel/contrib/database/data_sync/actions.py

- CreateDataSyncTableActionType · class · L29-L99 — class CreateDataSyncTableActionType(UndoableActionType)
- Params · class · L44-L50 — class Params
- do · method · L53-L84 — def do( cls, user: AbstractUser, database: Database, type_name: str, synced_properties: List[str], table_name: str, **kwargs: dict, ) -> DataSync
- scope · method · L87-L88 — def scope(cls, database_id) -> ActionScopeStr
- undo · method · L91-L93 — def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action)
- redo · method · L96-L99 — def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action)
- UpdateDataSyncTableActionType · class · L102-L161 — class UpdateDataSyncTableActionType(ActionType)
- Params · class · L116-L121 — class Params
- do · method · L124-L157 — def do( cls, user: AbstractUser, data_sync: DataSync, synced_properties: Optional[List[str]] = None, **kwargs: dict, ) -> DataSync
- scope · method · L160-L161 — def scope(cls, database_id) -> ActionScopeStr
- SyncDataSyncTableActionType · class · L164-L209 — class SyncDataSyncTableActionType(ActionType)
- Params · class · L174-L179 — class Params
- do · method · L182-L205 — def do( cls, user: AbstractUser, data_sync: DataSync, progress_builder: Optional[ChildProgressBuilder] = None, )
- scope · method · L208-L209 — def scope(cls, table_id: int) -> ActionScopeStr
