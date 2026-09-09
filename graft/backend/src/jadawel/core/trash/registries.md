# backend/src/jadawel/core/trash/registries.py

- TrashableItemType · class · L18-L170 — class TrashableItemType(ModelInstanceMixin, Instance, ABC)
- lookup_trashed_item · method · L23-L40 — def lookup_trashed_item( self, trashed_entry, trash_item_lookup_cache: Dict[str, Any] = None )
- permanently_delete_item · method · L43-L58 — def permanently_delete_item( self, trashed_item: Any, trash_item_lookup_cache: Dict[str, Any] = None, )
- requires_parent_id · method · L61-L67 — def requires_parent_id(self) -> bool
- get_parent · method · L70-L78 — def get_parent(self, trashed_item: Any) -> Optional[Any]
- restore · method · L81-L92 — def restore(self, trashed_item: Any, trash_entry)
- get_name · method · L95-L104 — def get_name(self, trashed_item: Any) -> str
- get_names · method · L106-L116 — def get_names(self, trashed_item: Any) -> str
- trash · method · L118-L136 — def trash( self, item_to_trash: Any, requesting_user: "AbstractUser", trash_entry: "TrashEntry", )
- get_restore_operation_type · method · L139-L147 — def get_restore_operation_type( self, ) -> str
- get_restore_operation_context · method · L149-L155 — def get_restore_operation_context(self, trash_entry, trashed_item) -> str
- get_owner · method · L157-L158 — def get_owner(self, trashed_item: Any) -> Optional["AbstractUser"]
- get_additional_restoration_data · method · L160-L170 — def get_additional_restoration_data(self, trashed_item: Any) -> Dict[str, Any]
- TrashOperationType · class · L173-L195 — class TrashOperationType(Instance, ABC)
- DefaultTrashOperationType · class · L198-L205 — class DefaultTrashOperationType(TrashOperationType)
- TrashableItemTypeRegistry · class · L208-L216 — class TrashableItemTypeRegistry(ModelRegistryMixin, Registry)
- TrashOperationTypeRegistry · class · L219-L227 — class TrashOperationTypeRegistry(ModelRegistryMixin, Registry)
