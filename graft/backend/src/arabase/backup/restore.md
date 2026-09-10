# backend/src/arabase/backup/restore.py

- RestoreError · class · L31-L32 — class RestoreError(Exception)
- RestoreResult · class · L36-L39 — class RestoreResult
- _pg_restore_path · function · L42-L55 — def _pg_restore_path() -> str: # Resolved the same way as pg_dump, and for the same reason: /usr/bin is # pg_wrapper, which picks a major version from the embedded cluster rather # than from the dump being restored. A dump written by a newer pg_dump is # unreadable by an older pg_restore, so the two must agree — taking the # newest installed version in both places is what makes them agree.
- redact · function · L58-L61 — def redact(database_url: str) -> str
- validate_target · function · L64-L88 — def validate_target(database_url: str, config: BackupConfig | None = None) -> None
- restore_backup · function · L91-L162 — def restore_backup(key: str, target_database_url: str) -> RestoreResult
