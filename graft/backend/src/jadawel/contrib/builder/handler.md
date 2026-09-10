# backend/src/jadawel/contrib/builder/handler.py

- BuilderHandler · class · L32-L152 — class BuilderHandler
- get_builder · method · L33-L55 — def get_builder(self, builder_id: int) -> Builder
- _get_builder_public_properties_version_cache · method · L58-L59 — def _get_builder_public_properties_version_cache(cls, builder: Builder) -> str
- get_builder_used_properties_cache_key · method · L61-L75 — def get_builder_used_properties_cache_key( self, user: Union[User, UserSourceUser], builder: Builder ) -> str
- invalidate_builder_public_properties_cache · method · L78-L81 — def invalidate_builder_public_properties_cache(cls, builder: Builder)
- get_builder_public_properties · method · L83-L114 — def get_builder_public_properties( self, user: UserSourceUser, builder: Builder ) -> Dict[str, Dict[int, List[str]]]
- compute_properties · function · L99-L101 — def compute_properties()
- get_published_applications · method · L116-L132 — def get_published_applications( self, workspace: Optional[Workspace] = None ) -> QuerySet[Builder]
- aggregate_user_source_counts · method · L134-L152 — def aggregate_user_source_counts( self, workspace: Optional[Workspace] = None, ) -> int
