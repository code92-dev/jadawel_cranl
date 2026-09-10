# backend/src/jadawel/contrib/database/migrations/0052_table_order_and_id_index.py

- split_identifier · function · L10-L21 — def split_identifier(identifier)
- names_digest · function · L24-L33 — def names_digest(*args, length)
- _django_index_name · function · L36-L38 — def _django_index_name(table, field_names)
- _copied_django_internal_index_name_calculator · function · L41-L73 — def _copied_django_internal_index_name_calculator(table_name, column_names, suffix="")
- _add_index_for_field · function · L76-L89 — def _add_index_for_field(schema_editor, table, field_names)
- _remove_index_for_field · function · L92-L94 — def _remove_index_for_field(schema_editor, table, field_names)
- forward · function · L98-L106 — def forward(apps, schema_editor)
- reverse · function · L110-L113 — def reverse(apps, schema_editor): # We can't safely rollback the indexes made above as we can't tell which ones were # created separately from this migration by django itself.
- Migration · class · L116-L125 — class Migration(migrations.Migration)
