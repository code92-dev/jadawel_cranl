# backend/src/arabase/mcp/protection/audit.py

- MCPMutationAuditContext · class · L10-L18 — class MCPMutationAuditContext
- is_content_blind_mcp_mutation · function · L26-L27 — def is_content_blind_mcp_mutation() -> bool
- content_blind_mcp_mutation · function · L31-L69 — def content_blind_mcp_mutation( *, endpoint, tool_type: str, table_id: int, row_count: int, policy_revision: int, access_generation: int, protected_field_ids: tuple[int, ...], ) -> Iterator[None]
