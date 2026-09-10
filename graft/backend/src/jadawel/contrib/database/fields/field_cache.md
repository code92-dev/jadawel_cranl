# backend/src/jadawel/contrib/database/fields/field_cache.py

- FieldCache · class · L8-L97 — class FieldCache
- __init__ · method · L18-L33 — def __init__( self, existing_cache: Optional["FieldCache"] = None, existing_model: Optional[Type[Model]] = None, )
- cache_model · method · L36-L38 — def cache_model(self, model: Type[Model])
- cache_model_fields · method · L41-L43 — def cache_model_fields(self, model: Type[Model])
- get_model · method · L45-L54 — def get_model(self, table)
- uncache_field · method · L56-L59 — def uncache_field(self, field)
- reset_cache · method · L61-L63 — def reset_cache(self)
- cache_field · method · L65-L77 — def cache_field(self, field)
- lookup_specific · method · L79-L88 — def lookup_specific(self, non_specific_field, fetch_if_missing=True)
- lookup_by_name · method · L90-L97 — def lookup_by_name(self, table, field_name: str)
