# backend/src/jadawel/contrib/automation/nodes/handler.py

- AutomationNodeHandler · class · L56-L576 — class AutomationNodeHandler(metaclass=jadawel_trace_methods(tracer))
- _get_node_cache_key · method · L66-L67 — def _get_node_cache_key(self, workflow, specific)
- get_nodes · method · L69-L117 — def get_nodes( self, workflow: AutomationWorkflow, specific: Optional[bool] = True, base_queryset: Optional[QuerySet] = None, with_cache: bool = True, ) -> Union[QuerySet[AutomationNode], Iterable[AutomationNode]]
- _get_nodes · function · L87-L110 — def _get_nodes(base_queryset=base_queryset)
- invalidate_node_cache · method · L119-L128 — def invalidate_node_cache(self, workflow)
- get_children · method · L130-L138 — def get_children(self, node: AutomationNode) -> List[AutomationNode]
- get_node · method · L140-L163 — def get_node( self, node_id: int, base_queryset: Optional[QuerySet] = None ) -> AutomationNode
- create_node · method · L165-L189 — def create_node( self, node_type: AutomationNodeType, workflow: AutomationWorkflow, **kwargs, ) -> AutomationNode
- update_node · method · L191-L208 — def update_node(self, node: AutomationNode, **kwargs) -> AutomationNode
- duplicate_node · method · L210-L241 — def duplicate_node(self, source_node: AutomationNode) -> AutomationNode
- export_node · method · L243-L262 — def export_node( self, node: AutomationNode, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, ) -> AutomationNodeDict
- import_node · method · L264-L291 — def import_node( self, workflow: AutomationWorkflow, serialized_node: AutomationNodeDict, id_mapping: Dict[str, Dict[int, int]], *args, **kwargs, ) -> AutomationNode
- import_nodes · method · L293-L343 — def import_nodes( self, workflow: AutomationWorkflow, serialized_nodes: List[AutomationNodeDict], id_mapping: Dict[str, Dict[int, int]], cache: Optional[Dict] = None, progress: Optional[ChildProgressBuilder] = None, *args, **kwargs, )
- import_node_only · method · L345-L365 — def import_node_only( self, workflow: AutomationWorkflow, serialized_node: AutomationNodeDict, id_mapping: Dict[str, Dict[int, int]], import_export_config: Optional[ImportExportConfig] = None, *args: Any, **kwargs: Any, ) -> AutomationNode
- _handle_workflow_error · method · L367-L387 — def _handle_workflow_error( self, node_history: AutomationNodeHistory, iteration_path: str, error: str, ) -> None
- _handle_simulation_notify · method · L389-L406 — def _handle_simulation_notify( self, simulate_until_node: AutomationNode | None, node: AutomationNode ) -> bool
- dispatch_node · method · L408-L576 — def dispatch_node( self, node_id: int, history_id: int, current_iterations: Optional[Dict[int, int]] = None, ) -> Signature | None
