# backend/src/jadawel/core/auth_provider/auth_provider_types.py

- AuthProviderType · class · L25-L187 — class AuthProviderType(BaseAuthProviderType)
- before_update · method · L30-L51 — def before_update( self, user: AbstractUser, auth_provider: AuthProviderModelSubClass, **values )
- before_delete · method · L53-L71 — def before_delete( self, user: AbstractUser, auth_provider: AuthProviderModelSubClass )
- get_or_create_user_and_sign_in · method · L73-L97 — def get_or_create_user_and_sign_in( self, auth_provider: AuthProviderModelSubClass, user_info: UserInfo ) -> [AbstractUser, bool]
- get_user_and_sign_in · method · L99-L141 — def get_user_and_sign_in( self, auth_provider: AuthProviderModelSubClass, user_info: UserInfo ) -> AbstractUser
- create_user · method · L143-L165 — def create_user( self, auth_provider: AuthProviderModelSubClass, user_info: UserInfo ) -> AbstractUser
- export_serialized · method · L167-L182 — def export_serialized(self) -> Dict[str, Any]
- import_serialized · method · L184-L187 — def import_serialized( self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict ) -> Any
- PasswordAuthProviderType · class · L190-L222 — class PasswordAuthProviderType(AuthProviderType)
- get_login_options · method · L213-L216 — def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]
- can_create_new_providers · method · L218-L219 — def can_create_new_providers(self, **kwargs)
- can_delete_existing_providers · method · L221-L222 — def can_delete_existing_providers(self)
