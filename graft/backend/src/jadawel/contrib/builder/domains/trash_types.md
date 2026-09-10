# backend/src/jadawel/contrib/builder/domains/trash_types.py

- DomainTrashableItemType · class · L11-L39 — class DomainTrashableItemType(TrashableItemType)
- get_parent · method · L15-L16 — def get_parent(self, trashed_item: Any) -> Optional[Any]
- get_name · method · L18-L19 — def get_name(self, trashed_item: Domain) -> str
- restore · method · L21-L27 — def restore(self, trashed_item: Domain, trash_entry: TrashEntry)
- permanently_delete_item · method · L29-L36 — def permanently_delete_item( self, trashed_item: Domain, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L38-L39 — def get_restore_operation_type(self) -> str
