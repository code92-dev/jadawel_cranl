# backend/src/jadawel/core/auth_provider/handler.py

- BaseAuthProviderHandler · class · L18-L145 — class BaseAuthProviderHandler
- get_auth_provider_by_id · method · L27-L48 — def get_auth_provider_by_id( cls, auth_provider_id: int, base_queryset: Optional[QuerySet] = None ) -> AuthProviderModelSubClass
- list_all_auth_providers · method · L51-L73 — def list_all_auth_providers( cls, base_queryset: Optional[QuerySet] = None, specific: bool = True, ) -> Iterable[AuthProviderModelSubClass]
- create_auth_provider · method · L76-L99 — def create_auth_provider( cls, user: AbstractUser, auth_provider_type: "BaseAuthProviderType", **values: Dict[str, Any], ) -> AuthProviderModelSubClass
- update_auth_provider · method · L102-L127 — def update_auth_provider( cls, user: AbstractUser, auth_provider: AuthProviderModelSubClass, **values: Dict[str, Any], ) -> AuthProviderModelSubClass
- delete_auth_provider · method · L130-L145 — def delete_auth_provider( cls, user: AbstractUser, auth_provider: AuthProviderModelSubClass )
- AuthProviderHandler · class · L148-L149 — class AuthProviderHandler(BaseAuthProviderHandler)
- PasswordProviderHandler · class · L152-L162 — class PasswordProviderHandler
- get · method · L154-L162 — def get(cls) -> PasswordAuthProviderModel
