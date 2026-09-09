# backend/tests/jadawel/contrib/database/rows/test_row_metadata_registry.py

- test_nothing_registered_returns_empty_even_when_rows_provided · function · L12-L17 — def test_nothing_registered_returns_empty_even_when_rows_provided()
- test_merges_together_row_metadata_by_type_and_row_id · function · L20-L57 — def test_merges_together_row_metadata_by_type_and_row_id()
- RowIdMetadata · class · L23-L32 — class RowIdMetadata(RowMetadataType)
- generate_metadata_for_rows · method · L26-L29 — def generate_metadata_for_rows( self, user, table, row_ids: List[int] ) -> Dict[int, Any]
- get_example_serializer_field · method · L31-L32 — def get_example_serializer_field(self) -> Field
- EvenRowsMetadata · class · L34-L43 — class EvenRowsMetadata(RowMetadataType)
- generate_metadata_for_rows · method · L37-L40 — def generate_metadata_for_rows( self, user, table, row_ids: List[int] ) -> Dict[int, Any]
- get_example_serializer_field · method · L42-L43 — def get_example_serializer_field(self) -> Field
