# backend/src/jadawel/core/captcha/handler.py

- CaptchaHandler · class · L12-L101 — class CaptchaHandler
- is_enabled · method · L14-L21 — def is_enabled() -> bool
- is_captcha_enabled_for · method · L24-L41 — def is_captcha_enabled_for(context: str) -> bool
- get_active_provider · method · L44-L71 — def get_active_provider() -> CaptchaProviderType
- validate_if_required · method · L74-L101 — def validate_if_required( context: str, token: str, remote_ip: Optional[str] = None, ) -> None
