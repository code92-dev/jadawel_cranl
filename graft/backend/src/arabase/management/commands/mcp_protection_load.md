# backend/src/arabase/management/commands/mcp_protection_load.py

- _connect · function · L40-L51 — def _connect(redis_url: str) -> Redis
- _issue_batch · function · L54-L107 — def _issue_batch(payload: tuple[str, int, int, int]) -> dict
- _redeem_sample · function · L110-L121 — def _redeem_sample(payload: tuple[str, dict]) -> bool
- _issuer_spike · function · L124-L144 — def _issuer_spike(payload: tuple[str, int, float]) -> dict
- _dead_issuer_worker · function · L147-L160 — def _dead_issuer_worker(payload: tuple[str, int]) -> None
- _delete_test_keys · function · L163-L166 — def _delete_test_keys(redis: Redis) -> None
- _redis_limits · function · L169-L175 — def _redis_limits(redis: Redis) -> tuple[int, int]
- Command · class · L178-L375 — class Command(BaseCommand)
- add_arguments · method · L181-L197 — def add_arguments(self, parser)
- handle · method · L199-L375 — def handle(self, *args, **options)
