# backend/tests/jadawel/core/mcp/test_mcp_registries.py

- EchoInput · class · L12-L13 — class EchoInput(BaseModel)
- EchoMCPTool · class · L16-L21 — class EchoMCPTool(MCPTool)
- _sync_call · method · L20-L21 — def _sync_call(self, endpoint, args)
- test_tool_call_preserves_behavior_without_interceptor · function · L24-L29 — def test_tool_call_preserves_behavior_without_interceptor(monkeypatch)
- test_tool_call_routes_validated_arguments_through_interceptor · function · L32-L52 — def test_tool_call_routes_validated_arguments_through_interceptor(monkeypatch)
- interceptor · function · L36-L38 — def interceptor(received_endpoint, tool, args, execute)
- test_tool_registry_rejects_a_second_call_interceptor · function · L55-L63 — def test_tool_registry_rejects_a_second_call_interceptor()
