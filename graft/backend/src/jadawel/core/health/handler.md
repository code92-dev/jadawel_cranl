# backend/src/jadawel/core/health/handler.py

- HealthCheckResult · class · L13-L15 — class HealthCheckResult(NamedTuple)
- HealthCheckHandler · class · L18-L104 — class HealthCheckHandler
- get_plugins · method · L20-L27 — def get_plugins(cls)
- run_all_checks · method · L30-L56 — def run_all_checks(cls) -> HealthCheckResult
- _should_skip_check · method · L59-L72 — def _should_skip_check(cls, plugin)
- send_test_email · method · L75-L104 — def send_test_email(cls, target_email: str)
