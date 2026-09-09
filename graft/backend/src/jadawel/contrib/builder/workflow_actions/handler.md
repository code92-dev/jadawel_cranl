# backend/src/jadawel/contrib/builder/workflow_actions/handler.py

- BuilderWorkflowActionHandler · class · L36-L195 — class BuilderWorkflowActionHandler(WorkflowActionHandler)
- get_workflow_actions · method · L40-L56 — def get_workflow_actions( self, page: Page, base_queryset: Optional[QuerySet] = None ) -> Iterable[WorkflowAction]
- get_builder_workflow_actions · method · L58-L71 — def get_builder_workflow_actions( self, builder: "Builder", base_queryset: QuerySet ) -> Iterable[WorkflowAction]
- update_workflow_action · method · L73-L83 — def update_workflow_action( self, workflow_action: BuilderWorkflowAction, **kwargs ) -> WorkflowAction: # When we are switching types we want to preserve the event and element and # page ids
- import_workflow_action · method · L85-L119 — def import_workflow_action( self, page: Page, serialized_workflow_action: Dict, id_mapping: Dict[str, Dict[int, int]], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict[str, any]] = None, **kwargs, )
- order_workflow_actions · method · L121-L145 — def order_workflow_actions( self, page: Page, order: List[int], base_qs=None, element: Element = None )
- create_workflow_action · method · L147-L171 — def create_workflow_action( self, workflow_action_type: WorkflowActionType, **kwargs ) -> BuilderWorkflowAction
- dispatch_workflow_action · method · L173-L195 — def dispatch_workflow_action( self, workflow_action: BuilderWorkflowServiceAction, dispatch_context: BuilderDispatchContext, ) -> DispatchResult
