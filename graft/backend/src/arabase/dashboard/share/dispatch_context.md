# backend/src/arabase/dashboard/share/dispatch_context.py

- get_public_allowed_properties · function · L44-L79 — def get_public_allowed_properties( dashboard: "Dashboard", ) -> Dict[int, List[str]]
- _widget_field_ids · function · L82-L99 — def _widget_field_ids(widget: "Widget", service: "Service") -> Set[int]
- _service_field_ids · function · L102-L128 — def _service_field_ids(service: "Service") -> Set[int]
- _ordered_schema_field_ids · function · L131-L159 — def _ordered_schema_field_ids(service: "Service") -> List[int]
- PublicDashboardDispatchContext · class · L162-L200 — class PublicDashboardDispatchContext(DashboardDispatchContext)
- __init__ · method · L175-L182 — def __init__( self, request: Optional[HttpRequest] = None, widget: Optional["Widget"] = None, allowed_properties: Optional[Dict[int, Iterable[str]]] = None, )
- public_allowed_properties · method · L185-L186 — def public_allowed_properties(self) -> Dict[str, Dict[int, List[str]]]
- clone · method · L188-L200 — def clone(self, **kwargs) -> Any: # The base implementation rebuilds the context from `own_properties` # alone, which drops the request the dashboard context requires.
