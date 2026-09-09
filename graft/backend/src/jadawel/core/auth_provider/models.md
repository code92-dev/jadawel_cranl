# backend/src/jadawel/core/auth_provider/models.py

- BaseAuthProviderModel · class · L12-L29 — class BaseAuthProviderModel( CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin, models.Model, WithRegistry )
- Meta · class · L28-L29 — class Meta
- AuthProviderModel · class · L32-L79 — class AuthProviderModel(BaseAuthProviderModel)
- get_type_registry · method · L47-L50 — def get_type_registry()
- user_signed_in · method · L52-L61 — def user_signed_in(self, user)
- get_next_provider_id · method · L64-L76 — def get_next_provider_id(cls) -> int
- Meta · class · L78-L79 — class Meta
- PasswordAuthProviderModel · class · L82-L82 — class PasswordAuthProviderModel(AuthProviderModel)
