# backend/src/arabase/mcp/protection/editing.py

- MCPProtectionPolicyConflict · class · L27-L28 — class MCPProtectionPolicyConflict(Exception)
- MCPProtectionPolicyNotReady · class · L31-L32 — class MCPProtectionPolicyNotReady(Exception)
- MCPProtectionPolicyEditResult · class · L36-L38 — class MCPProtectionPolicyEditResult
- replace_mcp_protection_policy · function · L41-L82 — def replace_mcp_protection_policy( *, user, endpoint_id: int, protected_field_ids: list[int], expected_revision: int, confirm_remove_field_ids: list[int], idempotency_key: str, ) -> MCPProtectionPolicyEditResult
- _replace_mcp_protection_policy · function · L86-L154 — def _replace_mcp_protection_policy( *, user, endpoint_id: int, protected_field_ids: list[int], expected_revision: int, confirm_remove_field_ids: list[int], idempotency_key: str, fingerprint: str, ) -> MCPProtectionPolicyEditResult
- reactivate_mcp_protection_policy · function · L158-L216 — def reactivate_mcp_protection_policy( *, user, endpoint_id: int, expected_revision: int ) -> MCPProtectionPolicy
- _request_fingerprint · function · L219-L235 — def _request_fingerprint( endpoint_id: int, protected_field_ids: list[int], expected_revision: int, confirm_remove_field_ids: list[int], ) -> str
