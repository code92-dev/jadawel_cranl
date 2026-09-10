# backend/src/jadawel/core/mcp/actions.py

- CreateMCPEndpointActionType · class · L17-L54 — class CreateMCPEndpointActionType(ActionType)
- Params · class · L32-L37 — class Params
- do · method · L40-L50 — def do(cls, user: AbstractUser, workspace: Workspace, name: str)
- scope · method · L53-L54 — def scope(cls, workspace_id: int)
- UpdateMCPEndpointActionType · class · L57-L102 — class UpdateMCPEndpointActionType(ActionType)
- Params · class · L72-L77 — class Params
- do · method · L80-L98 — def do(cls, user: AbstractUser, endpoint: MCPEndpoint, name: str)
- scope · method · L101-L102 — def scope(cls, workspace_id: int)
- DeleteMCPEndpointActionType · class · L105-L149 — class DeleteMCPEndpointActionType(ActionType)
- Params · class · L118-L123 — class Params
- do · method · L126-L145 — def do( cls, user: AbstractUser, endpoint: MCPEndpoint, )
- scope · method · L148-L149 — def scope(cls, workspace_id: int)
