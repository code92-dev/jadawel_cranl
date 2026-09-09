# backend/src/jadawel/contrib/database/migrations/0065_rename_old_generated_table_indexes.py

- split_identifier · function · L11-L22 — def split_identifier(identifier)
- names_digest · function · L25-L34 — def names_digest(*args, length)
- _copied_django_internal_index_name_calculator · function · L37-L69 — def _copied_django_internal_index_name_calculator(table_name, column_names, suffix="")
- _copied_django_index_class_naming_func · function · L72-L107 — def _copied_django_index_class_naming_func(table_name, column_names, suffix)
- forward · function · L111-L144 — def forward(apps, schema_editor)
- reverse · function · L148-L150 — def reverse(apps, schema_editor): # We can't safely rollback the index renames above
- Migration · class · L153-L162 — class Migration(migrations.Migration)
