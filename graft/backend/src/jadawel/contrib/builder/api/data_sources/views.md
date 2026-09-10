# backend/src/jadawel/contrib/builder/api/data_sources/views.py

- DataSourcesView · class · L83-L222 — class DataSourcesView(APIView)
- get_permissions · method · L86-L90 — def get_permissions(self)
- get · method · L122-L146 — def get(self, request, page_id)
- post · method · L192-L222 — def post(self, request, data: Dict, page_id: int)
- DataSourceView · class · L225-L384 — class DataSourceView(APIView)
- patch · method · L268-L343 — def patch(self, request, data_source_id: int)
- delete · method · L375-L384 — def delete(self, request, data_source_id: int)
- MoveDataSourceView · class · L387-L451 — class MoveDataSourceView(APIView)
- patch · method · L428-L451 — def patch(self, request, data: Dict, data_source_id: int)
- DispatchDataSourceView · class · L454-L523 — class DispatchDataSourceView(APIView)
- post · method · L506-L523 — def post(self, request, data_source_id: int)
- DispatchDataSourcesView · class · L526-L593 — class DispatchDataSourcesView(APIView)
- post · method · L559-L593 — def post(self, request, page_id: int)
- GetRecordNamesView · class · L596-L671 — class GetRecordNamesView(APIView)
- get · method · L650-L671 — def get(self, request, data_source_id: int): # Find the data source corresponding to the given id
