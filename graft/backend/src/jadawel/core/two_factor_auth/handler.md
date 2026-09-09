# backend/src/jadawel/core/two_factor_auth/handler.py

- TwoFactorAuthHandler · class · L18-L130 — class TwoFactorAuthHandler
- get_provider · method · L19-L40 — def get_provider( self, user: AbstractUser, base_queryset: QuerySet | None = None ) -> TwoFactorAuthProviderModel | None
- get_provider_for_update · method · L42-L67 — def get_provider_for_update( self, user: AbstractUser, ) -> TwoFactorProviderForUpdate | None
- configure_provider · method · L69-L97 — def configure_provider( self, provider_type_str: str, user: AbstractUser, **kwargs, ) -> TwoFactorAuthProviderModel
- disable · method · L99-L116 — def disable(self, user: AbstractUser, password: str)
- verify · method · L118-L130 — def verify(self, provider_type_str: str, **kwargs) -> bool
