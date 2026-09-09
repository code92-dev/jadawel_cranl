# backend/src/jadawel/contrib/builder/domains/handler.py

- DomainHandler · class · L27-L311 — class DomainHandler
- get_domain · method · L31-L54 — def get_domain( self, domain_id: int, base_queryset: QuerySet | None = None, for_update=False ) -> Domain
- get_domains · method · L56-L71 — def get_domains( self, builder: Builder, base_queryset: QuerySet = None ) -> Iterable[Domain]
- get_public_builder_by_domain_name · method · L73-L95 — def get_public_builder_by_domain_name(self, domain_name: str) -> Builder
- get_domain_for_builder · method · L97-L106 — def get_domain_for_builder(self, builder: Builder) -> Domain | None
- create_domain · method · L108-L143 — def create_domain( self, domain_type: DomainType, builder: Builder, **kwargs ) -> Domain
- delete_domain · method · L145-L152 — def delete_domain(self, domain: Domain)
- update_domain · method · L154-L185 — def update_domain(self, domain: Domain, **kwargs) -> Domain
- order_domains · method · L187-L209 — def order_domains( self, builder: Builder, order: List[int], base_qs=None ) -> List[int]
- get_published_domain_applications · method · L211-L231 — def get_published_domain_applications( self, workspace: Optional[Workspace] = None ) -> QuerySet[Builder]
- publish · method · L233-L303 — def publish(self, domain: Domain, progress: Progress | None = None)
- get_public_builder_by_domain_cache_key · method · L306-L307 — def get_public_builder_by_domain_cache_key(cls, domain_name: str) -> str
- invalidate_public_builder_by_domain_cache · method · L310-L311 — def invalidate_public_builder_by_domain_cache(cls, domain_name: str)
