# backend/src/jadawel/contrib/automation/workflows/service.py

- AutomationWorkflowService · class · L35-L357 — class AutomationWorkflowService
- __init__ · method · L36-L37 — def __init__(self)
- _validate_notification_recipients · method · L39-L50 — def _validate_notification_recipients(self, workspace, notification_recipient_ids)
- _map_notification_recipient_ids · method · L52-L63 — def _map_notification_recipient_ids(self, workspace, values)
- get_workflow · method · L65-L84 — def get_workflow(self, user: AbstractUser, workflow_id: int) -> AutomationWorkflow
- list_workflows · method · L86-L108 — def list_workflows( self, user: AbstractUser, automation_id: int ) -> List[AutomationWorkflow]
- create_workflow · method · L110-L149 — def create_workflow( self, user: AbstractUser, automation_id: int, name: str, notification_recipient_ids=None, ) -> AutomationWorkflow
- delete_workflow · method · L151-L176 — def delete_workflow( self, user: AbstractUser, workflow_id: int ) -> AutomationWorkflow
- update_workflow · method · L178-L208 — def update_workflow( self, user: AbstractUser, workflow_id: int, **kwargs ) -> UpdatedAutomationWorkflow
- order_workflows · method · L210-L246 — def order_workflows( self, user: AbstractUser, automation: Automation, order: List[int] ) -> List[int]
- duplicate_workflow · method · L248-L277 — def duplicate_workflow( self, user: AbstractUser, workflow: AutomationWorkflow, progress_builder: Optional[ChildProgressBuilder] = None, ) -> AutomationWorkflow
- async_publish · method · L279-L307 — def async_publish(self, user: AbstractUser, workflow_id: int) -> Job
- publish · method · L309-L331 — def publish( self, user: AbstractUser, workflow: AutomationWorkflow, progress: Progress ) -> None
- toggle_test_run · method · L333-L357 — def toggle_test_run( self, user: AbstractUser, workflow_id: int | None = None, simulate_until_node_id: int | None = None, )
