# backend/src/jadawel/contrib/builder/domains/service.py

- DomainService · class · L35-L281 — class DomainService
- __init__ · method · L36-L37 — def __init__(self)
- get_domain · method · L39-L70 — def get_domain( self, user: AbstractUser, domain_id: int, base_queryset: Optional[QuerySet] = None, for_update: bool = False, ) -> Domain
- get_domains · method · L72-L103 — def get_domains( self, user: AbstractUser, builder: Builder, base_queryset: Optional[QuerySet] = None, ) -> QuerySet[Domain]
- get_public_builder_by_domain_name · method · L105-L126 — def get_public_builder_by_domain_name(self, user: AbstractUser, domain_name: str)
- create_domain · method · L128-L156 — def create_domain( self, user: AbstractUser, domain_type: DomainType, builder: Builder, **kwargs, ) -> Domain
- delete_domain · method · L158-L177 — def delete_domain(self, user: AbstractUser, domain: Domain)
- update_domain · method · L179-L202 — def update_domain(self, user: AbstractUser, domain: Domain, **kwargs) -> Domain
- order_domains · method · L204-L235 — def order_domains( self, user: AbstractUser, builder: Builder, order: List[int] ) -> List[int]
- async_publish · method · L237-L259 — def async_publish(self, user: AbstractUser, domain: Domain)
- publish · method · L261-L281 — def publish(self, user: AbstractUser, domain: Domain, progress: Progress)
