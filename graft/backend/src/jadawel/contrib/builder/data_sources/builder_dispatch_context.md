# backend/src/jadawel/contrib/builder/data_sources/builder_dispatch_context.py

- BuilderDispatchContext · class · L32-L339 — class BuilderDispatchContext(DispatchContext)
- __init__ · method · L44-L85 — def __init__( self, request: HttpRequest, page: Page, workflow_action: Optional["WorkflowAction"] = None, data_source: Optional["DataSource"] = None, offset: Optional[int] = None, count: Optional[int] = None, only_expose_public_allowed_properties: Optional[bool] = True, **kwargs, )
- element · method · L88-L93 — def element(self) -> "Element"
- request_data · method · L96-L111 — def request_data(self) -> Dict
- data_provider_registry · method · L114-L115 — def data_provider_registry(self)
- element_type · method · L118-L128 — def element_type(self) -> Optional[Type["ElementType"]]
- get_timezone_name · method · L130-L137 — def get_timezone_name(self) -> str
- range · method · L139-L165 — def range(self, service)
- get_element_property_options · method · L167-L195 — def get_element_property_options(self) -> Dict[str, Dict[str, bool]]
- is_publicly_searchable · method · L198-L206 — def is_publicly_searchable(self) -> bool
- search_query · method · L208-L216 — def search_query(self) -> Optional[str]
- searchable_fields · method · L218-L232 — def searchable_fields(self) -> Optional[List[str]]
- is_publicly_filterable · method · L235-L243 — def is_publicly_filterable(self) -> bool
- filters · method · L245-L254 — def filters(self) -> Optional[str]
- is_publicly_sortable · method · L257-L265 — def is_publicly_sortable(self) -> bool
- sortings · method · L267-L275 — def sortings(self) -> Optional[str]
- validate_filter_search_sort_fields · method · L277-L313 — def validate_filter_search_sort_fields( self, fields: List[str], refinement: ServiceAdhocRefinements )
- public_allowed_properties · method · L316-L339 — def public_allowed_properties(self) -> Optional[Dict[str, Dict[int, List[str]]]]
