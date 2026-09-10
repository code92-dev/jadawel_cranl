# backend/src/jadawel/core/two_factor_auth/registries.py

- TwoFactorAuthProviderType · class · L35-L89 — class TwoFactorAuthProviderType( CustomFieldsInstanceMixin, ModelInstanceMixin, Instance, ABC, )
- configure · method · L42-L54 — def configure( self, user: AbstractUser, provider, **kwargs ) -> TwoFactorAuthProviderModel
- is_enabled · method · L57-L65 — def is_enabled(self, provider) -> bool
- verify · method · L68-L77 — def verify(self, **kwargs) -> bool
- disable · method · L80-L89 — def disable(self, provider, user)
- TOTPAuthProviderType · class · L92-L250 — class TOTPAuthProviderType(TwoFactorAuthProviderType)
- configure · method · L108-L172 — def configure( self, user: AbstractUser, provider: TOTPAuthProviderModel | None = None, **kwargs, ) -> TOTPAuthProviderModel
- store_backup_codes · method · L174-L182 — def store_backup_codes(self, provider, codes_plaintext)
- generate_backup_codes · method · L184-L197 — def generate_backup_codes(self)
- is_enabled · method · L199-L200 — def is_enabled(self, provider) -> bool
- verify · method · L202-L245 — def verify(self, **kwargs) -> bool
- disable · method · L247-L250 — def disable(self, provider, user)
- TwoFactorAuthTypeRegistry · class · L253-L264 — class TwoFactorAuthTypeRegistry( CustomFieldsRegistryMixin, ModelRegistryMixin[TwoFactorAuthProviderModel, TwoFactorAuthProviderType], Registry[TwoFactorAuthProviderType], )
