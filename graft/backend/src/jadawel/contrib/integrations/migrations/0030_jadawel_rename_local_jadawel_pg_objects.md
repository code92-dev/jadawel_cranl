# backend/src/jadawel/contrib/integrations/migrations/0030_jadawel_rename_local_jadawel_pg_objects.py

- _rename · function · L20-L70 — def _rename(from_token, to_token)
- forward · function · L73-L74 — def forward(apps, schema_editor)
- reverse · function · L77-L78 — def reverse(apps, schema_editor)
- Migration · class · L81-L91 — class Migration(migrations.Migration): # Every app that owns a renamed LocalJadawel model must have finished renaming # its tables before the dependent objects are swept.
