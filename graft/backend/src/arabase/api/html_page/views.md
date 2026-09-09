# backend/src/arabase/api/html_page/views.py

- _feed_response · function · L53-L70 — def _feed_response(rows_serializer_data, total_count: int, row_limit: int) -> Response
- HtmlPageViewRowsView · class · L73-L180 — class HtmlPageViewRowsView(APIView)
- get · method · L104-L180 — def get(self, request: Request, view_id: int, query_params) -> Response
- PublicHtmlPageViewRowsView · class · L183-L275 — class PublicHtmlPageViewRowsView(APIView)
- get · method · L225-L275 — def get(self, request: Request, slug: str, query_params) -> Response
- _artifact_endpoint_for_view · function · L278-L298 — def _artifact_endpoint_for_view(view: HtmlPageView)
