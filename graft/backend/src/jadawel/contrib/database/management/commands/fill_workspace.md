# backend/src/jadawel/contrib/database/management/commands/fill_workspace.py

- Command · class · L24-L160 — class Command(BaseCommand)
- add_arguments · method · L30-L91 — def add_arguments(self, parser)
- handle · method · L93-L160 — def handle(self, *args, **options)
- fill_workspace_with_data · function · L163-L247 — def fill_workspace_with_data( user, workspace: Workspace, database_count: int, table_count: int, token_count: int, avg_field_count: int, avg_row_count: int, percentage_variation: int = 0, )
