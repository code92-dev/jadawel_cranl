# backend/tests/jadawel/contrib/database/tokens/test_token_cache.py

- test_set_and_get_cached_token · function · L22-L35 — def test_set_and_get_cached_token(data_fixture)
- test_cached_token_omits_auth_secrets · function · L40-L54 — def test_cached_token_omits_auth_secrets(data_fixture)
- test_db_token_caching_disabled_when_ttl_is_zero · function · L59-L65 — def test_db_token_caching_disabled_when_ttl_is_zero(data_fixture)
- test_get_by_key_populates_cache_on_first_call · function · L70-L88 — def test_get_by_key_populates_cache_on_first_call(data_fixture)
- test_token_http_request_runs_no_queries_after_cache_warmup · function · L93-L120 — def test_token_http_request_runs_no_queries_after_cache_warmup( data_fixture, api_request_factory )
- _make_request · function · L103-L107 — def _make_request()
- test_token_save_invalidates_cache · function · L125-L136 — def test_token_save_invalidates_cache(data_fixture, django_capture_on_commit_callbacks)
- test_token_delete_invalidates_cache · function · L141-L154 — def test_token_delete_invalidates_cache( data_fixture, django_capture_on_commit_callbacks )
- test_rotate_token_key_invalidates_old_and_new_key · function · L159-L176 — def test_rotate_token_key_invalidates_old_and_new_key( data_fixture, django_capture_on_commit_callbacks )
- test_user_save_invalidates_token_cache · function · L181-L194 — def test_user_save_invalidates_token_cache( data_fixture, django_capture_on_commit_callbacks )
- test_user_profile_save_invalidates_token_cache · function · L199-L212 — def test_user_profile_save_invalidates_token_cache( data_fixture, django_capture_on_commit_callbacks )
