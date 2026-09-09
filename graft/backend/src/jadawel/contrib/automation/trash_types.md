# backend/src/jadawel/contrib/automation/trash_types.py

- AutomationTrashableItemType · class · L8-L47 — class AutomationTrashableItemType(TrashableItemType)
- get_parent · method · L12-L13 — def get_parent(self, trashed_item: Automation) -> Workspace
- get_name · method · L15-L16 — def get_name(self, trashed_item: Automation) -> str
- trash · method · L18-L31 — def trash( self, item_to_trash: Automation, requesting_user, trash_entry: TrashEntry, )
- restore · method · L33-L39 — def restore( self, trashed_item: Automation, trash_entry: TrashEntry, )
- permanently_delete_item · method · L41-L44 — def permanently_delete_item( self, trashed_item: Automation, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L46-L47 — def get_restore_operation_type(self) -> str
