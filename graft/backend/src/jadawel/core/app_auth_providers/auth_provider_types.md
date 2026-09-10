# backend/src/jadawel/core/app_auth_providers/auth_provider_types.py

- AppAuthProviderType · class · L16-L107 — class AppAuthProviderType( EasyImportExportMixin, PublicCustomFieldsInstanceMixin, BaseAuthProviderType )
- check_user_source_compatibility · method · L41-L63 — def check_user_source_compatibility(self, user_source)
- after_user_source_update · method · L65-L75 — def after_user_source_update( self, user: "AbstractUser", instance: AuthProviderModelSubClass, user_source: "UserSourceSubClass", )
- get_or_create_user_and_sign_in · method · L77-L88 — def get_or_create_user_and_sign_in( self, auth_provider: AuthProviderModelSubClass, user_info: UserInfo ) -> Tuple[AbstractUser, bool]
- get_pytest_params · method · L90-L99 — def get_pytest_params(self, pytest_data_fixture) -> dict[str, Any]
- apply_patch_pytest · method · L102-L107 — def apply_patch_pytest(self)
