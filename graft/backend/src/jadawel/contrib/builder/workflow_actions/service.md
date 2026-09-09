# backend/src/jadawel/contrib/builder/workflow_actions/service.py

- BuilderWorkflowActionService · class · L49-L340 — class BuilderWorkflowActionService
- __init__ · method · L50-L51 — def __init__(self)
- get_workflow_action · method · L53-L74 — def get_workflow_action( self, user: AbstractUser, workflow_action_id: int ) -> WorkflowAction
- get_workflow_actions · method · L76-L105 — def get_workflow_actions( self, user: AbstractUser, page: Page, ) -> List[WorkflowAction]
- get_builder_workflow_actions · method · L107-L127 — def get_builder_workflow_actions( self, user: AbstractUser, builder: "Builder", ) -> List[WorkflowAction]
- create_workflow_action · method · L129-L165 — def create_workflow_action( self, user: AbstractUser, workflow_action_type: BuilderWorkflowActionType, page: Page, **kwargs, ) -> WorkflowAction
- update_workflow_action · method · L167-L224 — def update_workflow_action( self, user: AbstractUser, workflow_action: WorkflowAction, **kwargs ) -> WorkflowAction
- delete_workflow_action · method · L226-L249 — def delete_workflow_action( self, user: AbstractUser, workflow_action: WorkflowAction )
- order_workflow_actions · method · L251-L292 — def order_workflow_actions( self, user: AbstractUser, page: Page, order: List[int], element: Element = None, ) -> List[int]
- dispatch_action · method · L294-L340 — def dispatch_action( self, user, workflow_action: BuilderWorkflowServiceAction, dispatch_context: BuilderDispatchContext, ) -> Any
