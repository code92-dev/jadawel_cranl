# backend/src/jadawel/api/integrations/views.py

- IntegrationsView · class · L52-L168 — class IntegrationsView(APIView)
- get_permissions · method · L55-L59 — def get_permissions(self)
- get · method · L91-L108 — def get(self, request, application_id)
- post · method · L151-L168 — def post(self, request, data: Dict, application_id: int)
- IntegrationView · class · L171-L276 — class IntegrationView(APIView)
- patch · method · L212-L235 — def patch(self, request, integration_id: int)
- delete · method · L267-L276 — def delete(self, request, integration_id: int)
- MoveIntegrationView · class · L279-L344 — class MoveIntegrationView(APIView)
- patch · method · L323-L344 — def patch(self, request, data: Dict, integration_id: int)
