# backend/src/jadawel/contrib/database/management/commands/copy_tables.py

- run · function · L11-L15 — def run(command, env): # Ignoring as this is a CLI admin tool calling Popen, we don't need to worry about # shell injection as to call this tool you must already have shell access...
- connection_string_from_django_connection · function · L18-L28 — def connection_string_from_django_connection(django_connection)
- copy_tables · function · L31-L121 — def copy_tables( batch_size: int, dry_run: bool, ssl: bool, source_connection, target_connection, logger: Callable[[str], None], command_runner: Callable[[str, Dict[str, Any]], None], )
- Command · class · L124-L179 — class Command(BaseCommand)
- add_arguments · method · L127-L158 — def add_arguments(self, parser)
- handle · method · L160-L179 — def handle(self, *args, **options)
