# backend/src/jadawel/core/captcha/registries.py

- CaptchaProviderType · class · L7-L47 — class CaptchaProviderType(Instance)
- is_configured · method · L13-L21 — def is_configured(self) -> bool
- get_frontend_config · method · L23-L31 — def get_frontend_config(self) -> dict
- validate_token · method · L33-L47 — def validate_token(self, token: str, remote_ip: Optional[str] = None) -> bool
- CaptchaProviderRegistry · class · L50-L52 — class CaptchaProviderRegistry(Registry[CaptchaProviderType])
