# backend/src/jadawel/core/search/search_types.py

- ApplicationSearchType · class · L13-L99 — class ApplicationSearchType(ModelSearchableItemType)
- get_base_queryset · method · L23-L40 — def get_base_queryset( self, user: "AbstractUser", workspace: "Workspace" ) -> QuerySet
- get_search_queryset · method · L42-L74 — def get_search_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext, ) -> QuerySet
- serialize_result · method · L76-L99 — def serialize_result( self, result: Application, user: "AbstractUser", workspace: "Workspace" ) -> Optional[SearchResult]
