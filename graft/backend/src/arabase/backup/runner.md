# backend/src/arabase/backup/runner.py

- dump_timeout_seconds · function · L28-L35 — def dump_timeout_seconds() -> int
- BackupError · class · L38-L39 — class BackupError(Exception)
- BackupResult · class · L43-L49 — class BackupResult
- client_binary · function · L56-L84 — def client_binary(name: str) -> str | None
- _pg_dump_path · function · L87-L97 — def _pg_dump_path() -> str
- _pg_dump_major_version · function · L100-L116 — def _pg_dump_major_version() -> int
- _server_major_version · function · L119-L121 — def _server_major_version() -> int: # Django exposes the server version as e.g. 150004 for 15.4.
- check_versions · function · L124-L143 — def check_versions() -> tuple[int, int]
- _dump_argv · function · L146-L155 — def _dump_argv(db: dict) -> list[str]
- _dump_to_file · function · L158-L201 — def _dump_to_file(path: str) -> int
- _client · function · L204-L213 — def _client(config: BackupConfig)
- _upload · function · L216-L229 — def _upload(client, config: BackupConfig, path: str, key: str) -> None: # No ACL unless one is configured. This used to send `private` # unconditionally, which fails against both of the targets most likely to # be used: Cloudflare R2 has no object ACLs, and an AWS bucket created # since April 2023 rejects the header outright. Neither made an object # public — they refused the upload — so the effect was a backup that never # ran rather than one exposed.
- _archive_media · function · L236-L258 — def _archive_media(path: str) -> int
- _prune · function · L261-L288 — def _prune(client, config: BackupConfig, now: datetime) -> list[str]
- run_backup · function · L291-L353 — def run_backup(config: BackupConfig | None = None) -> BackupResult
