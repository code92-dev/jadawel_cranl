# backend/src/jadawel/core/pgvector.py

- EmbeddingSchemaOperationType · class · L22-L24 — class EmbeddingSchemaOperationType(StrEnum)
- is_pgvector_enabled · function · L28-L38 — def is_pgvector_enabled() -> bool
- try_enable_pgvector · function · L41-L55 — def try_enable_pgvector() -> bool
- EmbeddingMixinManager · class · L58-L67 — class EmbeddingMixinManager(models.Manager)
- get_queryset · method · L59-L67 — def get_queryset(self)
- EmbeddingMixin · class · L70-L292 — class EmbeddingMixin(models.Model)
- _init_vector_field · method · L94-L102 — def _init_vector_field(cls) -> None
- try_init_vector_field · method · L105-L112 — def try_init_vector_field(cls) -> None
- can_search_vectors · method · L115-L117 — def can_search_vectors(cls) -> bool
- Meta · class · L119-L120 — class Meta
- _create_field_in_model · method · L124-L148 — def _create_field_in_model(cls, field: VectorField) -> None
- _add_vector_field_to_model · method · L151-L173 — def _add_vector_field_to_model(cls) -> VectorField
- _create_vector_index · method · L176-L200 — def _create_vector_index(cls) -> None
- _migrate_embedding_data · method · L204-L239 — def _migrate_embedding_data(cls) -> None
- is_vector_field_ready · method · L242-L257 — def is_vector_field_ready(cls) -> bool
- migrate_to_vector_field_if_needed · method · L260-L292 — def migrate_to_vector_field_if_needed(cls) -> None
- reset_vector_schema_operations · function · L295-L306 — def reset_vector_schema_operations() -> None
- try_migrate_vector_fields · function · L309-L351 — def try_migrate_vector_fields(sender, **kwargs)
