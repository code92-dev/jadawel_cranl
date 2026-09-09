# backend/src/jadawel/contrib/builder/domains/object_scopes.py

- BuilderDomainObjectScopeType · class · L15-L47 — class BuilderDomainObjectScopeType(ObjectScopeType)
- get_parent_scope · method · L19-L20 — def get_parent_scope(self) -> Optional["ObjectScopeType"]
- get_parent · method · L22-L23 — def get_parent(self, context: ContextObject) -> Optional[ContextObject]
- get_base_queryset · method · L25-L30 — def get_base_queryset(self, include_trash: bool = False) -> QuerySet
- get_enhanced_queryset · method · L32-L35 — def get_enhanced_queryset(self, include_trash: bool = False) -> QuerySet
- get_filter_for_scope_type · method · L37-L47 — def get_filter_for_scope_type(self, scope_type, scopes)
