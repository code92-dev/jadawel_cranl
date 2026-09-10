# backend/src/jadawel/core/services/dispatch_context.py

- DispatchContext · class · L10-L168 — class DispatchContext(RuntimeFormulaContext, ABC)
- __init__ · method · L26-L53 — def __init__( self, only_record_id=None, event_payload: Any = None, update_sample_data_for: Optional[List[Service]] = None, use_sample_data: bool = False, force_outputs: Dict[int, str] = None, )
- range · method · L56-L64 — def range(self, service: Service) -> tuple[int, int | None]
- clone · method · L66-L81 — def clone(self, **kwargs) -> RuntimeFormulaContextSubClass
- is_publicly_searchable · method · L85-L89 — def is_publicly_searchable(self) -> bool
- search_query · method · L92-L96 — def search_query(self) -> Optional[str]
- searchable_fields · method · L99-L105 — def searchable_fields(self) -> Optional[List[str]]
- is_publicly_filterable · method · L109-L113 — def is_publicly_filterable(self) -> bool
- filters · method · L116-L120 — def filters(self) -> Optional[str]
- is_publicly_sortable · method · L124-L128 — def is_publicly_sortable(self) -> bool
- sortings · method · L131-L135 — def sortings(self) -> Optional[str]
- public_allowed_properties · method · L139-L154 — def public_allowed_properties(self) -> Optional[Dict[str, Dict[int, List[str]]]]
- validate_filter_search_sort_fields · method · L157-L168 — def validate_filter_search_sort_fields( self, fields: List[str], refinement: ServiceAdhocRefinements )
