# backend/src/jadawel/core/prosemirror/utils.py

- is_valid_prosemirror_document · function · L13-L25 — def is_valid_prosemirror_document(json_doc: Dict[str, Any]) -> bool
- extract_mentioned_user_ids · function · L28-L46 — def extract_mentioned_user_ids(json_doc: Dict[str, Any]) -> Set[int]
- _extract_mentions · function · L40-L42 — def _extract_mentions(node, *args)
- extract_mentioned_users_in_workspace · function · L49-L65 — def extract_mentioned_users_in_workspace( json_doc: Dict[str, Any], workspace: Workspace ) -> QuerySet[AbstractUser]
- prosemirror_doc_from_plain_text · function · L68-L84 — def prosemirror_doc_from_plain_text(plain_text_message) -> Dict[str, Any]
- prosemirror_doc_to_plain_text · function · L87-L99 — def prosemirror_doc_to_plain_text(json_doc: Dict[str, Any]) -> str
- _to_plain_text · function · L95-L96 — def _to_plain_text(node)
