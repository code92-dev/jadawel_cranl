# backend/src/jadawel/contrib/automation/workflows/trash_types.py

- AutomationWorkflowTrashableItemType · class · L13-L51 — class AutomationWorkflowTrashableItemType(TrashableItemType)
- get_parent · method · L17-L18 — def get_parent(self, trashed_item: AutomationWorkflow) -> any
- get_name · method · L20-L21 — def get_name(self, trashed_item: AutomationWorkflow) -> str
- trash · method · L23-L35 — def trash( self, item_to_trash: AutomationWorkflow, requesting_user, trash_entry: TrashEntry, )
- restore · method · L37-L43 — def restore( self, trashed_item: AutomationWorkflow, trash_entry: TrashEntry, )
- permanently_delete_item · method · L45-L48 — def permanently_delete_item( self, trashed_item: AutomationWorkflow, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L50-L51 — def get_restore_operation_type(self) -> str
