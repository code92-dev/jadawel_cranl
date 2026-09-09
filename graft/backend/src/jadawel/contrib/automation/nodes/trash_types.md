# backend/src/jadawel/contrib/automation/nodes/trash_types.py

- AutomationNodeTrashableItemType · class · L21-L113 — class AutomationNodeTrashableItemType(TrashableItemType)
- get_parent · method · L25-L26 — def get_parent(self, trashed_item: AutomationActionNode) -> AutomationWorkflow
- get_name · method · L28-L29 — def get_name(self, trashed_item: AutomationActionNode) -> str
- get_additional_restoration_data · method · L31-L33 — def get_additional_restoration_data(self, trashed_item: AutomationActionNode): # We save the previous position for the restoration
- trash · method · L35-L54 — def trash( self, item_to_trash: AutomationActionNode, requesting_user: AbstractUser, trash_entry: TrashEntry, )
- restore · method · L56-L105 — def restore( self, trashed_item: AutomationActionNode, trash_entry: TrashEntry, )
- permanently_delete_item · method · L107-L110 — def permanently_delete_item( self, trashed_item: AutomationNode, trash_item_lookup_cache=None )
- get_restore_operation_type · method · L112-L113 — def get_restore_operation_type(self) -> str
