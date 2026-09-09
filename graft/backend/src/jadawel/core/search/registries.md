# backend/src/jadawel/core/search/registries.py

- SearchableItemType · class · L14-L139 — class SearchableItemType(ModelInstanceMixin, Instance)
- __init__ · method · L27-L30 — def __init__(self)
- get_base_queryset · method · L32-L43 — def get_base_queryset( self, user: "AbstractUser", workspace: "Workspace" ) -> models.QuerySet
- get_search_queryset · method · L45-L60 — def get_search_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext, ) -> models.QuerySet
- get_union_values_queryset · method · L62-L75 — def get_union_values_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext, ) -> QuerySet
- execute_search · method · L77-L101 — def execute_search( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext ) -> List[SearchResult]
- postprocess · method · L103-L125 — def postprocess(self, rows: Iterable[Dict]) -> List[SearchResult]
- serialize_result · method · L127-L139 — def serialize_result( self, item: models.Model, user: "AbstractUser", workspace: "Workspace" ) -> Optional[SearchResult]
- WorkspaceSearchRegistry · class · L142-L147 — class WorkspaceSearchRegistry(Registry)
