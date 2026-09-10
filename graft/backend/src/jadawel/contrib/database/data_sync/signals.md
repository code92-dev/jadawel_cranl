# backend/src/jadawel/contrib/database/data_sync/signals.py

- before_field_deleted · function · L10-L20 — def before_field_deleted( sender, field_id, field, user, allow_deleting_primary=False, **kwargs ): # This typically happens when the table is trashed, and then we do want to allow it.
