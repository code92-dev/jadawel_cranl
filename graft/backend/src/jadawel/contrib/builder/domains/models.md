# backend/src/jadawel/contrib/builder/domains/models.py

- validate_domain · function · L24-L37 — def validate_domain(value: str)
- get_default_domain_content_type · function · L40-L41 — def get_default_domain_content_type()
- Domain · class · L44-L103 — class Domain( HierarchicalModelMixin, TrashableModelMixin, OrderableMixin, WithRegistry, PolymorphicContentTypeMixin, models.Model, )
- get_parent · method · L80-L81 — def get_parent(self)
- Meta · class · L83-L84 — class Meta
- get_public_url · method · L86-L94 — def get_public_url(self)
- get_last_order · method · L97-L99 — def get_last_order(cls, builder)
- get_type_registry · method · L102-L103 — def get_type_registry() -> ModelRegistryMixin
- CustomDomain · class · L106-L107 — class CustomDomain(Domain)
- SubDomain · class · L110-L111 — class SubDomain(Domain)
- PublishDomainJob · class · L114-L115 — class PublishDomainJob(JobWithUserIpAddress, Job)
