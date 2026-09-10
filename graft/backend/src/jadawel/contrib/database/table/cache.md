# backend/src/jadawel/contrib/database/table/cache.py

- table_model_cache_entry_key · function · L34-L35 — def table_model_cache_entry_key(table_id: int) -> str
- get_cached_model_field_attrs · function · L38-L45 — def get_cached_model_field_attrs(table: "Table") -> Optional[Dict[str, Any]]
- set_cached_model_field_attrs · function · L48-L54 — def set_cached_model_field_attrs(table: "Table", field_attrs: Dict[str, Any])
- clear_generated_model_cache · function · L57-L68 — def clear_generated_model_cache()
- invalidate_table_in_model_cache · function · L71-L87 — def invalidate_table_in_model_cache(table_id: int)
