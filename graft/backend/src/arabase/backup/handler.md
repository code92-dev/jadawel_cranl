# backend/src/arabase/backup/handler.py

- BackupHealth · class · L27-L38 — class BackupHealth
- healthy · method · L37-L38 — def healthy(self) -> bool
- parse_crontab · function · L41-L49 — def parse_crontab(expression: str) -> celery_crontab
- next_run_on · function · L52-L60 — def next_run_on(schedule: BackupSchedule, now: Optional[datetime] = None)
- record_run · function · L64-L77 — def record_run(trigger: str = BackupRun.TRIGGER_SCHEDULED)
- get_health · function · L80-L121 — def get_health(now: Optional[datetime] = None) -> BackupHealth
- health · function · L92-L99 — def health(status, errors=None)
- republish_schedule · function · L124-L165 — def republish_schedule() -> None
