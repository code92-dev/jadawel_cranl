# backend/src/jadawel/contrib/database/airtable/utils.py

- extract_share_id_from_url · function · L15-L33 — def extract_share_id_from_url(public_base_url: str) -> str
- get_airtable_row_primary_value · function · L36-L52 — def get_airtable_row_primary_value(table, row)
- get_airtable_column_name · function · L55-L68 — def get_airtable_column_name(raw_airtable_table, column_id) -> str
- unknown_value_to_human_readable · function · L71-L87 — def unknown_value_to_human_readable(value: Any) -> str
- parse_json_and_remove_invalid_surrogate_characters · function · L90-L111 — def parse_json_and_remove_invalid_surrogate_characters(response: Response) -> dict
- quill_parse_inline · function · L114-L128 — def quill_parse_inline(insert, attributes)
- quill_wrap_block · function · L131-L156 — def quill_wrap_block(attributes)
- quill_split_with_newlines · function · L159-L165 — def quill_split_with_newlines(value)
- quill_to_markdown · function · L168-L245 — def quill_to_markdown(ops: list) -> str
- flush_line · function · L192-L197 — def flush_line()
- flush_multi_line · function · L199-L210 — def flush_multi_line(current_prepend, current_append)
- airtable_date_filter_value_to_jadawel · function · L248-L274 — def airtable_date_filter_value_to_jadawel(value: Optional[Union[dict, str]]) -> str
- skip_filter_if_type_duration_and_value_too_high · function · L277-L299 — def skip_filter_if_type_duration_and_value_too_high(raw_airtable_column, value)
