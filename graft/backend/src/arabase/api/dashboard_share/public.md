# backend/src/arabase/api/dashboard_share/public.py

- PublicDashboardInfoView · class · L77-L130 — class PublicDashboardInfoView(APIView)
- get · method · L97-L130 — def get(self, request: Request, slug: str) -> Response
- PublicDashboardDispatchView · class · L133-L204 — class PublicDashboardDispatchView(APIView)
- post · method · L183-L204 — def post(self, request: Request, slug: str, data_source_id: int) -> Response
- PublicDashboardAuthThrottle · class · L207-L226 — class PublicDashboardAuthThrottle(SimpleRateThrottle)
- get_cache_key · method · L222-L226 — def get_cache_key(self, request: Request, view) -> str
- PublicDashboardAuthView · class · L229-L272 — class PublicDashboardAuthView(APIView)
- post · method · L254-L272 — def post(self, request: Request, data: dict, slug: str) -> Response
