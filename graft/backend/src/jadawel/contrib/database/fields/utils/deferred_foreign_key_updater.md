# backend/src/jadawel/contrib/database/fields/utils/deferred_foreign_key_updater.py

- DeferredForeignKeyUpdater · class · L9-L67 — class DeferredForeignKeyUpdater
- __init__ · method · L25-L26 — def __init__(self)
- add_deferred_fk_to_update · method · L28-L37 — def add_deferred_fk_to_update( self, instance: "Model", fk_attr: str, original_fk_id: int, mapping_key: str, )
- run_deferred_fk_updates · method · L39-L67 — def run_deferred_fk_updates( self, id_mapping: Dict[str, Dict[int, int]], run_mapping_key: str )
