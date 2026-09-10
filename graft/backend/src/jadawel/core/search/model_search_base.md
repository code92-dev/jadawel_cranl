# backend/src/jadawel/core/search/model_search_base.py

- ModelSearchableItemType · class · L16-L85 — class ModelSearchableItemType(SearchableItemType)
- build_search_query · method · L25-L31 — def build_search_query(self, query: str) -> Q
- get_base_queryset · method · L33-L36 — def get_base_queryset( self, user: "AbstractUser", workspace: "Workspace" ) -> models.QuerySet
- get_search_queryset · method · L38-L45 — def get_search_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext ) -> models.QuerySet
- build_payload · method · L47-L48 — def build_payload(self)
- build_title_annotation · method · L50-L51 — def build_title_annotation(self)
- build_subtitle_annotation · method · L53-L54 — def build_subtitle_annotation(self)
- get_union_values_queryset · method · L56-L85 — def get_union_values_queryset( self, user: "AbstractUser", workspace: "Workspace", context: SearchContext ) -> models.QuerySet
