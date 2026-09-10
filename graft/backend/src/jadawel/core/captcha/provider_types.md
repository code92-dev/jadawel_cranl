# backend/src/jadawel/core/captcha/provider_types.py

- CloudflareTurnstileCaptchaProviderType · class · L16-L52 — class CloudflareTurnstileCaptchaProviderType(CaptchaProviderType)
- is_configured · method · L19-L23 — def is_configured(self) -> bool
- get_frontend_config · method · L25-L28 — def get_frontend_config(self) -> dict
- validate_token · method · L30-L52 — def validate_token(self, token: str, remote_ip: Optional[str] = None) -> bool
