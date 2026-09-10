# backend/src/jadawel/core/two_factor_auth/models.py

- TwoFactorAuthProviderModel · class · L11-L41 — class TwoFactorAuthProviderModel( CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin, WithRegistry, models.Model )
- get_type_registry · method · L32-L37 — def get_type_registry()
- is_enabled · method · L40-L41 — def is_enabled(self)
- TOTPAuthProviderModel · class · L44-L56 — class TOTPAuthProviderModel(TwoFactorAuthProviderModel)
- backup_codes · method · L51-L52 — def backup_codes(self)
- is_enabled · method · L55-L56 — def is_enabled(self)
- TOTPUsedCode · class · L59-L74 — class TOTPUsedCode(models.Model)
- Meta · class · L68-L74 — class Meta
- TwoFactorAuthRecoveryCode · class · L77-L86 — class TwoFactorAuthRecoveryCode(models.Model)
