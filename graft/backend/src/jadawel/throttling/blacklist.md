# backend/src/jadawel/throttling/blacklist.py

- _token_key · function · L21-L22 — def _token_key(raw_token: str) -> str
- _ip_key · function · L25-L26 — def _ip_key(ip: str) -> str
- _remaining_ttl · function · L29-L31 — def _remaining_ttl(expires_at: float) -> int | None
- _resolve_ttl · function · L34-L37 — def _resolve_ttl(ttl: int | None) -> int | None
- blacklist_token · function · L40-L44 — def blacklist_token(raw_token: str, ttl: int | None = None) -> None
- blacklist_ip · function · L47-L51 — def blacklist_ip(ip: str, ttl: int | None = None) -> None
- get_token_cooldown_time · function · L54-L60 — def get_token_cooldown_time(raw_token: str) -> int | None
- is_ip_blacklisted · function · L63-L69 — def is_ip_blacklisted(ip: str) -> int | None
