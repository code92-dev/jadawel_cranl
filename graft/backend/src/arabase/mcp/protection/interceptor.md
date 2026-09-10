# backend/src/arabase/mcp/protection/interceptor.py

- intercept_mcp_tool_call · function · L39-L153 — def intercept_mcp_tool_call( endpoint: MCPEndpoint, tool: MCPTool, args: Any, execute: Callable[[], Any], ) -> Any
- _lock_policy_snapshot · function · L156-L176 — def _lock_policy_snapshot(endpoint: MCPEndpoint, snapshot) -> None
- _reject_token_envelopes · function · L179-L189 — def _reject_token_envelopes(value: Any) -> None
- _prepare_update_for_protected_cells · function · L192-L351 — def _prepare_update_for_protected_cells(endpoint, args, policy)
- restore · function · L343-L349 — def restore() -> None
- _contains_token_marker · function · L354-L361 — def _contains_token_marker(value: Any) -> bool
- _row_payload · function · L364-L372 — def _row_payload(row: Any) -> Any
