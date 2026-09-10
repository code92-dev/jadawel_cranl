# backend/src/jadawel/contrib/automation/history/handler.py

- AutomationHistoryHandler · class · L20-L145 — class AutomationHistoryHandler
- get_workflow_histories · method · L21-L45 — def get_workflow_histories( self, workflow: AutomationWorkflow, base_queryset: Optional[QuerySet] = None ) -> QuerySet[AutomationWorkflowHistory]
- get_workflow_history · method · L47-L68 — def get_workflow_history( self, history_id: int, base_queryset: Optional[QuerySet] = None ) -> AutomationWorkflowHistory
- create_workflow_history · method · L70-L94 — def create_workflow_history( self, original_workflow: AutomationWorkflow, workflow: AutomationWorkflow, started_on: datetime, is_test_run: bool, event_payload: Optional[Union[Dict, List[Dict]]] = None, simulate_until_node: Optional[AutomationNode] = None, status: HistoryStatusChoices = HistoryStatusChoices.STARTED, completed_on: Optional[datetime] = None, message: str = "", ) -> AutomationWorkflowHistory
- create_node_history · method · L96-L114 — def create_node_history( self, workflow_history: AutomationWorkflowHistory, node: AutomationNode, started_on: datetime, status: HistoryStatusChoices = HistoryStatusChoices.STARTED, completed_on: Optional[datetime] = None, message: str = "", ) -> AutomationNodeHistory
- create_node_result · method · L116-L129 — def create_node_result( self, node_history: AutomationNodeHistory, result: Optional[Union[Dict, List[Dict]]] = None, iteration_path: str = "", ) -> AutomationNodeResult
- get_node_result · method · L131-L145 — def get_node_result(self, history, node, iteration_path)
