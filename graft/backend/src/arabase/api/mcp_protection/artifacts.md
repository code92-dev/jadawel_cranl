# backend/src/arabase/api/mcp_protection/artifacts.py

- _get_endpoint_and_view · function · L29-L37 — def _get_endpoint_and_view(request, endpoint_id: int, view_id: int)
- ArtifactDraftView · class · L40-L58 — class ArtifactDraftView(APIView)
- post · method · L45-L58 — def post(self, request, data)
- ArtifactDraftApprovalView · class · L61-L70 — class ArtifactDraftApprovalView(APIView)
- post · method · L69-L70 — def post(self, request, draft_id: int)
- ArtifactRevokeView · class · L73-L90 — class ArtifactRevokeView(APIView)
- post · method · L83-L90 — def post(self, request, view_id: int, data)
- ArtifactStateView · class · L93-L99 — class ArtifactStateView(APIView)
- get · method · L97-L99 — def get(self, request, view_id: int)
