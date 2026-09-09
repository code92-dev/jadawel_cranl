# backend/src/jadawel/contrib/database/search_base.py

- DatabaseSearchableItemType · class · L16-L126 — class DatabaseSearchableItemType(ModelSearchableItemType)
- build_search_query · method · L25-L43 — def build_search_query(self, query: str) -> Q
- get_search_queryset · method · L45-L72 — def get_search_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext, ) -> models.QuerySet
- build_payload · method · L74-L79 — def build_payload(self)
- build_title_annotation · method · L81-L82 — def build_title_annotation(self)
- build_subtitle_annotation · method · L84-L85 — def build_subtitle_annotation(self)
- get_union_values_queryset · method · L87-L126 — def get_union_values_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext, ) -> models.QuerySet
