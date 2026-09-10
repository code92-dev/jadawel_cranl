# backend/src/jadawel/core/app_auth_providers/handler.py

- AppAuthProviderHandler · class · L16-L109 — class AppAuthProviderHandler(BaseAuthProviderHandler)
- list_app_auth_providers_for_user_source · method · L20-L36 — def list_app_auth_providers_for_user_source( cls, user_source: "UserSource", **kwargs )
- create_app_auth_provider · method · L39-L58 — def create_app_auth_provider( cls, user: AbstractUser, auth_provider_type: AppAuthProviderType, user_source: "UserSource", **kwargs, )
- export_app_auth_provider · method · L61-L74 — def export_app_auth_provider( cls, app_auth_provider: AppAuthProviderType, files_zip=None, storage=None, cache=None, )
- import_app_auth_provider · method · L77-L109 — def import_app_auth_provider( cls, user_source: "UserSource", serialized_app_auth_provider: Dict, id_mapping: Dict, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache=None, )
