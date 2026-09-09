# backend/src/jadawel/contrib/database/migrations/0041_add_generated_table_indexes.py

- split_identifier · function · L8-L19 — def split_identifier(identifier)
- names_digest · function · L22-L31 — def names_digest(*args, length)
- _django_index_name · function · L34-L36 — def _django_index_name(table, field_name)
- _copied_django_internal_index_name_calculator · function · L39-L71 — def _copied_django_internal_index_name_calculator(table_name, column_names, suffix="")
- forward · function · L75-L89 — def forward(apps, schema_editor)
- _add_index_for_field · function · L92-L103 — def _add_index_for_field(schema_editor, table, field_name)
- reverse · function · L107-L110 — def reverse(apps, schema_editor): # We can't safely rollback the indexes made above as we can't tell which ones were # created separately from this migration by django itself.
- Migration · class · L113-L122 — class Migration(migrations.Migration)
