# backend/tests/jadawel/core/test_throttling.py

- clear_throttle_cache · function · L19-L24 — def clear_throttle_cache()
- get_named_mock · function · L27-L31 — def get_named_mock(function_name)
- NamedMagicMock · class · L28-L29 — class NamedMagicMock(mock.MagicMock)
- fn_rate_limited_one_per_second · function · L35-L41 — def fn_rate_limited_one_per_second()
- test_rate_limit_throws_exception_by_default · function · L44-L47 — def test_rate_limit_throws_exception_by_default(clear_throttle_cache)
- test_rate_limit_with_ignored_exceptions · function · L50-L58 — def test_rate_limit_with_ignored_exceptions(clear_throttle_cache)
- test_rate_limit_different_keys_independent_counters · function · L61-L67 — def test_rate_limit_different_keys_independent_counters(clear_throttle_cache)
- test_rate_limit_different_functions_independent_counters · function · L70-L78 — def test_rate_limit_different_functions_independent_counters(clear_throttle_cache)
- test_rate_limit_per_seconds · function · L81-L97 — def test_rate_limit_per_seconds(clear_throttle_cache)
- test_rate_limit_per_minute · function · L100-L116 — def test_rate_limit_per_minute(clear_throttle_cache)
- test_rate_limit_per_hour · function · L119-L135 — def test_rate_limit_per_hour(clear_throttle_cache)
