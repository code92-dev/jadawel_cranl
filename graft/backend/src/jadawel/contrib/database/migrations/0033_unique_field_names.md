# backend/src/jadawel/contrib/database/migrations/0033_unique_field_names.py

- forward · function · L9-L14 — def forward(apps, schema_editor)
- fix_fields_with_duplicate_names · function · L17-L31 — def fix_fields_with_duplicate_names(Field, Table)
- fix_fields_with_reserved_names · function · L34-L54 — def fix_fields_with_reserved_names(Field, Table)
- rename_non_unique_names_in_table · function · L57-L103 — def rename_non_unique_names_in_table( Field, table_id, name_to_fix, start_index, next_name_number, new_name_prefix )
- find_next_unused_field_name · function · L106-L128 — def find_next_unused_field_name(field_name, start_index, existing_collisions)
- reverse · function · L132-L135 — def reverse(apps, schema_editor)
- Migration · class · L138-L150 — class Migration(migrations.Migration)
