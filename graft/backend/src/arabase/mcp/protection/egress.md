# backend/src/arabase/mcp/protection/egress.py

- table_has_protected_output · function · L33-L45 — def table_has_protected_output( table_id: int, protected_fields, workspace_id: int ) -> bool
- mask_direct_row_output · function · L48-L150 — def mask_direct_row_output( endpoint: MCPEndpoint, args: Any, result: Any, policy: MCPProtectionPolicyState, ) -> Any
- _protected_output_fields · function · L153-L241 — def _protected_output_fields( table_id: int, direct_fields, protected_fields, workspace_id: int )
- visit · function · L193-L207 — def visit(field_id: int) -> None
- _OutputField · class · L244-L261 — class _OutputField
- __init__ · method · L247-L249 — def __init__(self, *, binding, operation_class: str)
- field_id · method · L252-L253 — def field_id(self)
- field_name · method · L256-L257 — def field_name(self)
- field_type · method · L260-L261 — def field_type(self)
- _assert_policy_unchanged · function · L264-L284 — def _assert_policy_unchanged( endpoint: MCPEndpoint, snapshot: MCPProtectionPolicyState ) -> None
- _is_empty_value · function · L287-L292 — def _is_empty_value(value: Any) -> bool
- _raise_protection_unavailable · function · L295-L296 — def _raise_protection_unavailable() -> Never
