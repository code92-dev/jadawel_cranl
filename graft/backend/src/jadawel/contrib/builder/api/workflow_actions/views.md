# backend/src/jadawel/contrib/builder/api/workflow_actions/views.py

- BuilderWorkflowActionsView · class · L78-L190 — class BuilderWorkflowActionsView(APIView)
- get_permissions · method · L81-L85 — def get_permissions(self)
- post · method · L129-L142 — def post(self, request, data: Dict, page_id: int)
- get · method · L176-L190 — def get(self, request, page_id: int)
- BuilderWorkflowActionView · class · L193-L300 — class BuilderWorkflowActionView(APIView)
- delete · method · L225-L234 — def delete(self, request, workflow_action_id: int)
- patch · method · L277-L300 — def patch(self, request, workflow_action_id: int)
- OrderBuilderWorkflowActionsView · class · L303-L355 — class OrderBuilderWorkflowActionsView(APIView)
- post · method · L344-L355 — def post(self, request, data: Dict, page_id: int)
- DispatchBuilderWorkflowActionView · class · L358-L420 — class DispatchBuilderWorkflowActionView(APIView)
- post · method · L399-L420 — def post(self, request, workflow_action_id: int)
