# backend/src/jadawel/api/admin/users/views.py

- UsersAdminView · class · L45-L117 — class UsersAdminView(AdminListingView)
- get_queryset · method · L58-L61 — def get_queryset(self, request)
- get · method · L72-L82 — def get(self, request)
- post · method · L111-L117 — def post(self, request, data) -> Response
- UserAdminView · class · L120-L217 — class UserAdminView(APIView)
- patch · method · L161-L172 — def patch(self, request, user_id, data)
- delete · method · L206-L217 — def delete(self, request, user_id)
- UserAdminImpersonateView · class · L220-L269 — class UserAdminImpersonateView(GenericAPIView)
- post · method · L253-L269 — def post(self, request)
