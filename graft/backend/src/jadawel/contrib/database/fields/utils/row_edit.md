# backend/src/jadawel/contrib/database/fields/utils/row_edit.py

- _get_row_edit_signer · function · L11-L12 — def _get_row_edit_signer()
- generate_row_edit_token · function · L15-L28 — def generate_row_edit_token(view_slug: str, field_id: int, cell_uuid: str) -> str
- build_row_edit_url · function · L31-L43 — def build_row_edit_url(cell_uuid: str, form_view: "FormView", field_id: int) -> str
- verify_and_decode_edit_token · function · L46-L58 — def verify_and_decode_edit_token(token: str) -> Optional[Dict[str, str]]
