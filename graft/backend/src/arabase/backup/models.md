# backend/src/arabase/backup/models.py

- BackupSchedule · class · L43-L76 — class BackupSchedule(models.Model)
- Meta · class · L60-L61 — class Meta
- get_solo · method · L64-L68 — def get_solo(cls) -> "BackupSchedule"
- crontab · method · L71-L72 — def crontab(self) -> str
- grace_period · method · L75-L76 — def grace_period(self) -> timedelta
- BackupRun · class · L79-L154 — class BackupRun(models.Model)
- Meta · class · L126-L127 — class Meta
- __str__ · method · L129-L130 — def __str__(self)
- duration_seconds · method · L133-L136 — def duration_seconds(self) -> float | None
- mark_succeeded · method · L138-L146 — def mark_succeeded(self, result) -> None
- mark_failed · method · L148-L154 — def mark_failed(self, exc: BaseException) -> None
