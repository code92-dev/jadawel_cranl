# backend/src/jadawel/core/workflow_actions/handler.py

- WorkflowActionHandler · class · L16-L157 — class WorkflowActionHandler(ABC)
- model · method · L24-L25 — def model(self) -> Type[WorkflowAction]
- registry · method · L29-L30 — def registry(self) -> Registry
- get_workflow_action · method · L32-L46 — def get_workflow_action(self, workflow_action_id: int) -> WorkflowAction
- get_all_workflow_actions · method · L48-L68 — def get_all_workflow_actions( self, base_queryset: Optional[QuerySet] = None ) -> Iterable[WorkflowAction]
- create_workflow_action · method · L70-L90 — def create_workflow_action( self, workflow_action_type: WorkflowActionType, **prepared_values ) -> WorkflowAction
- delete_workflow_action · method · L92-L99 — def delete_workflow_action(self, workflow_action: WorkflowAction)
- update_workflow_action · method · L101-L137 — def update_workflow_action( self, workflow_action: WorkflowAction, **prepared_values ) -> WorkflowAction
- export_workflow_action · method · L139-L157 — def export_workflow_action( self, workflow_action, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, )
