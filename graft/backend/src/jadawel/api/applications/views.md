# backend/src/jadawel/api/applications/views.py

- AllApplicationsView · class · L59-L100 — class AllApplicationsView(APIView)
- get · method · L77-L100 — def get(self, request)
- ApplicationsView · class · L103-L225 — class ApplicationsView(APIView)
- get_permissions · method · L106-L110 — def get_permissions(self)
- get · method · L143-L162 — def get(self, request, workspace_id)
- post · method · L202-L225 — def post(self, request, data, workspace_id)
- ApplicationView · class · L228-L391 — class ApplicationView(APIView)
- get · method · L262-L271 — def get(self, request, application_id)
- patch · method · L309-L342 — def patch(self, request, application_id)
- delete · method · L379-L391 — def delete(self, request, application_id)
- OrderApplicationsView · class · L394-L442 — class OrderApplicationsView(APIView)
- post · method · L435-L442 — def post(self, request, data, workspace_id)
- AsyncDuplicateApplicationView · class · L445-L500 — class AsyncDuplicateApplicationView(APIView)
- post · method · L488-L500 — def post(self, request: Request, application_id: int) -> Response
