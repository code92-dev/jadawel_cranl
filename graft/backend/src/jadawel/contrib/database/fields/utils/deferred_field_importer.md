# backend/src/jadawel/contrib/database/fields/utils/deferred_field_importer.py

- DeferredFieldImporter · class · L10-L128 — class DeferredFieldImporter
- __init__ · method · L18-L20 — def __init__(self)
- _unique_field_name · method · L22-L23 — def _unique_field_name(self, table_id: int, field_name: str) -> str
- add_deferred_field_import · method · L25-L48 — def add_deferred_field_import( self, table: "Table", field_name: str, field_dependencies: Set[Tuple[str, str]], import_field_callback: Callable, ) -> None
- get_all_fields_dependencies · method · L50-L90 — def get_all_fields_dependencies( self, field_name_fields_mapping: Dict[int, Dict[str, "Field"]] ) -> Dict[str, Set[str]]
- run_deferred_field_imports · method · L92-L128 — def run_deferred_field_imports( self, field_name_fields_mapping: Dict[int, Dict[str, "Field"]] ) -> List["Field"]
