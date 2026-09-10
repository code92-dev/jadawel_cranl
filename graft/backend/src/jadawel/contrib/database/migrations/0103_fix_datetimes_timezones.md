# backend/src/jadawel/contrib/database/migrations/0103_fix_datetimes_timezones.py

- forward · function · L14-L36 — def forward(apps, schema_editor): # since all the datetimes saved in the database are in UTC, we need to set the # `date_force_timezone` to UTC for all the fields and set `date_show_tzinfo` to # True so the user can be aware of the timezone.
- Migration · class · L39-L46 — class Migration(migrations.Migration)
