# backend/src/jadawel/contrib/database/api/views/grid/views.py

- get_available_aggregation_type · function · L107-L108 — def get_available_aggregation_type()
- GridViewView · class · L111-L371 — class GridViewView(APIView)
- get_permissions · method · L114-L118 — def get_permissions(self)
- get · method · L215-L300 — def get(self, request, view_id, field_options, row_metadata, query_params)
- post · method · L345-L371 — def post(self, request, view_id, data)
- GridViewFieldAggregationsView · class · L374-L482 — class GridViewFieldAggregationsView(APIView)
- get_permissions · method · L377-L381 — def get_permissions(self)
- get · method · L449-L482 — def get(self, request, view_id, total, query_params)
- PublicGridViewFieldAggregationsView · class · L485-L591 — class PublicGridViewFieldAggregationsView(APIView)
- get · method · L553-L591 — def get(self, request, slug, total, query_params)
- GridViewFieldAggregationView · class · L594-L701 — class GridViewFieldAggregationView(APIView)
- get_permissions · method · L597-L601 — def get_permissions(self)
- get · method · L672-L701 — def get(self, request, view_id, field_id, total)
- PublicGridViewRowsView · class · L704-L865 — class PublicGridViewRowsView(APIView)
- get · method · L807-L865 — def get( self, request: Request, slug: str, field_options: bool, query_params ) -> Response
