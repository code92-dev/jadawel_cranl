# backend/src/jadawel/core/mcp/handler.py

- MCPEndpointHandler · class · L22-L196 — class MCPEndpointHandler
- get_by_key · method · L23-L42 — def get_by_key(self, key: str) -> MCPEndpoint
- get_endpoint · method · L44-L83 — def get_endpoint( self, user: AbstractUser, endpoint_id: int, base_queryset: QuerySet = None ) -> MCPEndpoint
- generate_unique_key · method · L85-L111 — def generate_unique_key(self, length: int = 32, max_tries: int = 1000) -> str
- create_endpoint · method · L113-L140 — def create_endpoint( self, user: AbstractUser, workspace: Workspace, name: str ) -> MCPEndpoint
- update_endpoint · method · L142-L172 — def update_endpoint( self, user: AbstractUser, endpoint: MCPEndpoint, name: str ) -> MCPEndpoint
- delete_endpoint · method · L174-L196 — def delete_endpoint(self, user: AbstractUser, endpoint: MCPEndpoint)
