# backend/src/jadawel/core/mcp/registries.py

- MCPTool · class · L17-L102 — class MCPTool(Instance)
- name · method · L40-L42 — def name(self) -> str
- get_name · method · L44-L45 — def get_name(self) -> str
- list · method · L47-L65 — async def list(self, endpoint: MCPEndpoint) -> List["Tool"]
- call · method · L67-L90 — async def call( self, endpoint: MCPEndpoint, call_arguments: Dict[str, Any], ) -> Sequence[Union["TextContent", "ImageContent", "EmbeddedResource"]]
- _sync_call · method · L92-L102 — def _sync_call(self, endpoint: MCPEndpoint, args: Any) -> Any
- MCPToolRegistry · class · L105-L152 — class MCPToolRegistry(Registry[MCPTool])
- __init__ · method · L108-L112 — def __init__(self)
- call_sync · method · L114-L120 — def call_sync(self, tool: MCPTool, endpoint: MCPEndpoint, args: Any) -> Any
- register_call_interceptor · method · L122-L132 — def register_call_interceptor( self, interceptor: Callable[[MCPEndpoint, MCPTool, Any, Callable[[], Any]], Any], ) -> None
- call_interceptor · method · L135-L138 — def call_interceptor( self, ) -> Callable[[MCPEndpoint, MCPTool, Any, Callable[[], Any]], Any] | None
- list_all_tools · method · L140-L148 — async def list_all_tools(self, endpoint: MCPEndpoint) -> List["Tool"]
- match_by_name · method · L150-L152 — def match_by_name(self, name: str) -> Optional[MCPTool]
