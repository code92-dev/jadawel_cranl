# backend/src/jadawel/core/management/backup/backup_runner.py

- JadawelBackupRunner · class · L24-L270 — class JadawelBackupRunner
- __init__ · method · L30-L52 — def __init__( self, host: str, database: str, username: str, port: Optional[str] = "5432", jobs: Optional[int] = 1, )
- backup_jadawel · method · L54-L91 — def backup_jadawel( self, backup_file_name: Optional[str] = None, batch_size: Optional[int] = 60, additional_pg_dump_args: Optional[List[str]] = None, ) -> str
- restore_jadawel · method · L93-L133 — def restore_jadawel( self, backup_file_name: str, additional_pg_restore_args: Optional[List[str]] = None, )
- _build_pg_dump_command · method · L135-L136 — def _build_pg_dump_command(self, extra_command: List[str]) -> List[str]
- _get_postgres_tool_args · method · L138-L152 — def _get_postgres_tool_args(self) -> List[str]
- _build_pg_restore_command · method · L154-L155 — def _build_pg_restore_command(self, extra_command: List[str]) -> List[str]
- _build_connection · method · L157-L163 — def _build_connection(self)
- _backup_everything_but_user_tables · method · L165-L180 — def _backup_everything_but_user_tables( self, temporary_directory_name: str, additional_pg_dump_args: List[str], )
- _backup_user_tables_in_batches · method · L182-L213 — def _backup_user_tables_in_batches( self, batch_size: int, output_directory: str, additional_pg_dump_args: List[str], )
- _restore_everything_but_user_tables · method · L215-L228 — def _restore_everything_but_user_tables( self, extracted_backup_location: Path, additional_pg_restore_args: List[str], )
- _restore_user_tables_from_batch_back_ups · method · L230-L244 — def _restore_user_tables_from_batch_back_ups( self, extracted_backup_location: Path, additional_pg_restore_args: List[str], )
- _open_files_and_run_backup · method · L246-L263 — def _open_files_and_run_backup( self, backup_file_name: str, batch_size: int, additional_pg_dump_args: List[str], )
- _run_command_in_sub_process · method · L266-L270 — def _run_command_in_sub_process(self, command)
- _get_sorted_user_tables_names · function · L273-L310 — def _get_sorted_user_tables_names(conn) -> List[str]
- _default_backup_location · function · L313-L315 — def _default_backup_location(database)
- add_shared_postgres_command_args · function · L318-L356 — def add_shared_postgres_command_args(parser)
