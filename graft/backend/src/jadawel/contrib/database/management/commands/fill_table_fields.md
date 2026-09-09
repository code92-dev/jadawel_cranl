# backend/src/jadawel/contrib/database/management/commands/fill_table_fields.py

- Command · class · L14-L61 — class Command(BaseCommand)
- add_arguments · method · L17-L40 — def add_arguments(self, parser)
- handle · method · L42-L61 — def handle(self, *args, **options)
- _get_or_create_form_view · function · L64-L68 — def _get_or_create_form_view(table: Table) -> FormView
- fill_table_fields · function · L71-L102 — def fill_table_fields(limit, table, shuffle_fields=False)
- create_field_for_every_type · function · L105-L123 — def create_field_for_every_type(table)
