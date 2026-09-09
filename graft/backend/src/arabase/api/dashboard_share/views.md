# backend/src/arabase/api/dashboard_share/views.py

- _get_dashboard_for_sharing · function · L46-L54 — def _get_dashboard_for_sharing(request: Request, dashboard_id: int) -> Dashboard
- DashboardShareView · class · L57-L125 — class DashboardShareView(APIView)
- get · method · L75-L81 — def get(self, request: Request, dashboard_id: int) -> Response
- post · method · L100-L103 — def post(self, request: Request, dashboard_id: int) -> Response
- delete · method · L122-L125 — def delete(self, request: Request, dashboard_id: int) -> Response
- DashboardShareRotateSlugView · class · L128-L158 — class DashboardShareRotateSlugView(APIView)
- post · method · L154-L158 — def post(self, request: Request, dashboard_id: int) -> Response
- DashboardSharePasswordView · class · L161-L192 — class DashboardSharePasswordView(APIView)
- patch · method · L188-L192 — def patch(self, request: Request, data: dict, dashboard_id: int) -> Response
