# backend/src/jadawel/core/mcp/__init__.py

- _safe_tool_error · function · L19-L37 — def _safe_tool_error(code: MCPErrorCode, *, retryable: bool, correlation_id: UUID)
- JadawelMCPServer · class · L40-L236 — class JadawelMCPServer
- __init__ · method · L53-L64 — def __init__(self)
- _setup_handlers · method · L66-L78 — def _setup_handlers(self)
- return_empty · method · L80-L86 — async def return_empty(self) -> list
- get_endpoint · method · L88-L106 — async def get_endpoint(self)
- call_tool · method · L108-L157 — async def call_tool(self, name: str, arguments)
- list_tools · method · L159-L168 — async def list_tools(self) -> list["Tool"]
- sse_app · method · L170-L236 — def sse_app(self) -> "Starlette"
- handle_sse · function · L186-L221 — async def handle_sse(request: Request) -> None
- get_jadawel_mcp_server · function · L242-L246 — def get_jadawel_mcp_server() -> JadawelMCPServer
