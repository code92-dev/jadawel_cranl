# backend/src/jadawel/core/two_factor_auth/actions.py

- ConfigureTwoFactorAuthActionType · class · L16-L65 — class ConfigureTwoFactorAuthActionType(ActionType)
- Params · class · L30-L34 — class Params
- do · method · L37-L61 — def do( cls, user: AbstractUser, provider_type: str, **kwargs ) -> TwoFactorAuthProviderModel
- scope · method · L64-L65 — def scope(cls) -> ActionScopeStr
- DisableTwoFactorAuthActionType · class · L68-L102 — class DisableTwoFactorAuthActionType(ActionType)
- Params · class · L79-L81 — class Params
- do · method · L84-L98 — def do(cls, user: AbstractUser, password: str) -> None
- scope · method · L101-L102 — def scope(cls) -> ActionScopeStr
