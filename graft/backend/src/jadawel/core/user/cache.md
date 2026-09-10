# backend/src/jadawel/core/user/cache.py

- _cache_key · function · L14-L15 — def _cache_key(user_id: int) -> str
- get_cached_user · function · L18-L26 — def get_cached_user(user_id: int) -> AbstractUser | None
- set_cached_user · function · L29-L41 — def set_cached_user(user: AbstractUser) -> None
- invalidate_cached_user · function · L44-L52 — def invalidate_cached_user(user_id: int) -> None
