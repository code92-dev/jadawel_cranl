# backend/src/jadawel/contrib/database/table/receivers.py

- on_rows_created · function · L20-L23 — def on_rows_created(sender, rows, before, user, table, **kwargs)
- on_rows_deleted · function · L27-L30 — def on_rows_deleted(sender, rows, user, table, **kwargs)
- on_rows_updated · function · L34-L44 — def on_rows_updated( sender, rows, user, table, model, before_return, updated_field_ids, **kwargs ): # If a file field has been updated, let's recalculate the storage usage at the first # opportunity.
- on_table_created · function · L49-L53 — def on_table_created(sender, table, user, **kwargs): # If rows have been created or imported, they will be counted in the `rows_created` # signal, so let's only create an empty placehorder to make sure the table usage # will be updated avoiding double counting.
- on_table_deleted · function · L57-L61 — def on_table_deleted(sender, table, user, **kwargs)
- on_application_created · function · L66-L73 — def on_application_created(sender, application, **kwargs)
- on_field_restored · function · L78-L80 — def on_field_restored(sender, field, **kwargs)
