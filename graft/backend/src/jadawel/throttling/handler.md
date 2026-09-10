# backend/src/jadawel/throttling/handler.py

- _get_redis_cli · function · L53-L54 — def _get_redis_cli()
- ConcurrentUserRequestsThrottle · class · L57-L211 — class ConcurrentUserRequestsThrottle(SimpleRateThrottle)
- __new__ · method · L68-L71 — def __new__(cls, *args, **kwargs)
- _init_redis_cli · method · L74-L78 — def _init_redis_cli(cls)
- _get_ip · method · L81-L82 — def _get_ip(cls, request) -> str
- _debug · method · L85-L92 — def _debug(cls, request, log_msg, request_id=None, **kwargs)
- parse_rate · method · L94-L96 — def parse_rate(self, rate)
- get_cache_key · method · L99-L128 — def get_cache_key(cls, request, view=None) -> str | None
- allow_request · method · L130-L150 — def allow_request(self, request, view)
- _allow · method · L152-L163 — def _allow(self, request, request_id, count, limit)
- _raise_deny_exc · method · L165-L190 — def _raise_deny_exc(self, request, request_id, count, limit)
- _blacklist · method · L193-L199 — def _blacklist(cls, request, ttl: int | None = None) -> None
- on_request_processed · method · L202-L208 — def on_request_processed(cls, request)
- wait · method · L210-L211 — def wait(self)
- rate_limit · function · L214-L256 — def rate_limit(rate: RateLimit, key: str, raise_exception: bool = True)
- decorator · function · L230-L254 — def decorator(func)
- wrapper · function · L232-L252 — def wrapper(*args, **kwargs)
