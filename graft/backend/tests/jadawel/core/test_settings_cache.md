# backend/tests/jadawel/core/test_settings_cache.py

- test_set_and_get_cached_settings · function · L19-L30 — def test_set_and_get_cached_settings()
- test_caching_disabled_when_ttl_is_zero · function · L35-L39 — def test_caching_disabled_when_ttl_is_zero()
- test_invalidate_cached_settings · function · L44-L50 — def test_invalidate_cached_settings()
- test_signal_invalidates_cache_on_settings_save · function · L55-L64 — def test_signal_invalidates_cache_on_settings_save(django_capture_on_commit_callbacks)
- test_get_settings_uses_cache_on_second_call · function · L69-L79 — def test_get_settings_uses_cache_on_second_call()
- test_get_settings_always_hits_db_when_cache_disabled · function · L84-L93 — def test_get_settings_always_hits_db_when_cache_disabled()
