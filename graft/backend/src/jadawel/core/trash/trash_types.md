# backend/src/jadawel/core/trash/trash_types.py

- ApplicationTrashableItemType · class · L14-L52 — class ApplicationTrashableItemType(TrashableItemType)
- get_parent · method · L18-L19 — def get_parent(self, trashed_item: Any) -> Optional[Any]
- get_name · method · L21-L22 — def get_name(self, trashed_item: Application) -> str
- restore · method · L24-L34 — def restore( self, trashed_item: Application, trash_entry: TrashEntry, )
- permanently_delete_item · method · L36-L49 — def permanently_delete_item( self, trashed_item: Application, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L51-L52 — def get_restore_operation_type(self) -> str
- WorkspaceTrashableItemType · class · L55-L95 — class WorkspaceTrashableItemType(TrashableItemType)
- get_parent · method · L59-L60 — def get_parent(self, trashed_item: Any) -> Optional[Any]
- get_name · method · L62-L63 — def get_name(self, trashed_item: Workspace) -> str
- restore · method · L65-L72 — def restore(self, trashed_item: Workspace, trash_entry: TrashEntry)
- permanently_delete_item · method · L74-L92 — def permanently_delete_item( self, trashed_workspace: Workspace, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L94-L95 — def get_restore_operation_type(self) -> str
