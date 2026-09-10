# backend/src/jadawel/contrib/database/api/fields/views.py

- FieldsView · class · L160-L379 — class FieldsView(APIView)
- get_permissions · method · L164-L168 — def get_permissions(self)
- get · method · L208-L273 — def get(self, request, table_id, query_params)
- post · method · L349-L379 — def post(self, request, data, table_id)
- FieldView · class · L382-L581 — class FieldView(APIView)
- get · method · L415-L427 — def get(self, request, field_id)
- patch · method · L500-L526 — def patch(self, request, field_id)
- delete · method · L571-L581 — def delete(self, request, field_id)
- UniqueRowValueFieldView · class · L584-L641 — class UniqueRowValueFieldView(APIView)
- get · method · L629-L641 — def get(self, request, field_id, query_params)
- AsyncDuplicateFieldView · class · L644-L697 — class AsyncDuplicateFieldView(APIView)
- post · method · L686-L697 — def post(self, request: Request, field_id: int, data: Dict[str, Any]) -> Response
- ChangePrimaryFieldView · class · L700-L773 — class ChangePrimaryFieldView(APIView)
- post · method · L754-L773 — def post(self, request: Request, table_id: int, data: Dict[str, Any]) -> Response
- PasswordFieldAuthenticationView · class · L776-L841 — class PasswordFieldAuthenticationView(APIView)
- post · method · L816-L841 — def post(self, request: Request, data: Dict[str, Any]) -> Response
