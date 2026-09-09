# backend/src/arabase/api/mcp_protection/views.py

- _may_display_field_metadata · function · L59-L69 — def _may_display_field_metadata(user, field) -> bool
- MCPProtectionPolicyView · class · L72-L187 — class MCPProtectionPolicyView(APIView)
- get · method · L84-L98 — def get(self, request: Request, endpoint_id: int) -> Response
- patch · method · L110-L132 — def patch(self, request: Request, endpoint_id: int, data: dict) -> Response
- post · method · L151-L166 — def post(self, request: Request, endpoint_id: int, data: dict) -> Response
- delete · method · L182-L187 — def delete(self, request: Request, endpoint_id: int) -> Response
- MCPProtectionReadinessView · class · L190-L208 — class MCPProtectionReadinessView(APIView)
- get · method · L200-L208 — def get(self, request: Request) -> Response
- MCPEndpointProtectionSummariesView · class · L211-L293 — class MCPEndpointProtectionSummariesView(APIView)
- get · method · L219-L260 — def get(self, request: Request) -> Response: # Owners see their own endpoints. Workspace administrators additionally # receive the content-blind status/count projection for suspended or # blocked endpoints in their workspaces, which is all the cleanup path # needs and never includes a key or protected value.
- post · method · L276-L293 — def post(self, request: Request, data: dict) -> Response
