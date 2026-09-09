# backend/src/jadawel/contrib/automation/automation_dispatch_context.py

- AutomationDispatchContext · class · L18-L144 — class AutomationDispatchContext(DispatchContext)
- __init__ · method · L21-L71 — def __init__( self, workflow: AutomationWorkflow, history: AutomationNodeHistory, event_payload: Optional[Union[Dict, List[Dict]]] = None, simulate_until_node: Optional[AutomationActionNode] = None, current_iterations: Optional[Dict[int, int]] = None, )
- clone · method · L73-L76 — def clone(self, **kwargs)
- get_iteration_path · method · L78-L84 — def get_iteration_path(self, node)
- _get_previous_result_cache_key · method · L86-L87 — def _get_previous_result_cache_key(self, node) -> Optional[str]
- data_provider_registry · method · L90-L91 — def data_provider_registry(self)
- get_previous_node_result · method · L93-L101 — def get_previous_node_result(self, node) -> Dict[int, Any]: # We don't need to cache per iteration path because it won't change in this # dispatch
- get_timezone_name · method · L103-L109 — def get_timezone_name(self) -> str
- range · method · L111-L112 — def range(self, service: Service)
- sortings · method · L114-L115 — def sortings(self) -> Optional[str]
- filters · method · L117-L118 — def filters(self) -> Optional[str]
- is_publicly_sortable · method · L121-L122 — def is_publicly_sortable(self) -> bool
- is_publicly_filterable · method · L125-L126 — def is_publicly_filterable(self) -> bool
- is_publicly_searchable · method · L129-L130 — def is_publicly_searchable(self) -> bool
- public_allowed_properties · method · L133-L134 — def public_allowed_properties(self) -> Optional[Dict[str, Dict[int, List[str]]]]
- search_query · method · L136-L137 — def search_query(self) -> Optional[str]
- searchable_fields · method · L139-L140 — def searchable_fields(self)
- validate_filter_search_sort_fields · method · L142-L144 — def validate_filter_search_sort_fields( self, fields: List[str], refinement: ServiceAdhocRefinements )
