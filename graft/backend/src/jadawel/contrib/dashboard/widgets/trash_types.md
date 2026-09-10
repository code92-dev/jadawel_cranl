# backend/src/jadawel/contrib/dashboard/widgets/trash_types.py

- WidgetTrashableItemType · class · L11-L38 — class WidgetTrashableItemType(TrashableItemType)
- get_parent · method · L15-L16 — def get_parent(self, trashed_item: Widget) -> any
- get_name · method · L18-L19 — def get_name(self, trashed_item: Widget) -> str
- trash · method · L21-L24 — def trash(self, item_to_trash: Widget, requesting_user, trash_entry: TrashEntry)
- restore · method · L26-L30 — def restore(self, trashed_item: Widget, trash_entry: TrashEntry)
- permanently_delete_item · method · L32-L35 — def permanently_delete_item( self, trashed_item: Widget, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L37-L38 — def get_restore_operation_type(self) -> str
