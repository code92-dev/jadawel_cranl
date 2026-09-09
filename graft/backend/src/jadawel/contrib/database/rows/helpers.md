# backend/src/jadawel/contrib/database/rows/helpers.py

- construct_entry_from_action_and_diff · function · L18-L40 — def construct_entry_from_action_and_diff( user: AbstractUser, action: ActionData, fields_metadata: Dict[str, Any], row_diff: RowChangeDiff, )
- extract_row_diff · function · L43-L87 — def extract_row_diff( table_id: int, row_id: int, fields_metadata: Dict[str, Any], before_values: Dict[str, Any], after_values: Dict[str, Any], are_equal: Optional[Callable] = None, ) -> Optional[RowChangeDiff]
- are_equal · function · L58-L61 — def are_equal(field_identifier, after_value, before_value) -> bool
- raise_if_ids_mismatch · function · L90-L100 — def raise_if_ids_mismatch(before_values, after_values, fields_metadata)
- update_related_tables_entries · function · L103-L181 — def update_related_tables_entries( related_rows_diff: RelatedRowsDiff, fields_metadata: Dict[str, Any], row_diff: RowChangeDiff, ) -> RelatedRowsDiff
- _init_linked_row_diff · function · L129-L138 — def _init_linked_row_diff(linked_field_id)
- _update_linked_row_diff · function · L140-L159 — def _update_linked_row_diff( field_metadata: Dict[str, Any], row_ids_set: set[int], key: str )
- construct_related_rows_entries · function · L184-L231 — def construct_related_rows_entries( related_rows_diff: RelatedRowsDiff, user: AbstractUser, action: ActionData, ) -> List[RowHistory]
