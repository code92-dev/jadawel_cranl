# backend/src/jadawel/contrib/database/ws/table/signals.py

- table_created · function · L19-L29 — def table_created(sender, table, user, **kwargs)
- table_updated · function · L33-L54 — def table_updated( sender, table: Table, user: AbstractUser, force_table_refresh: bool = False, **kwargs, )
- table_deleted · function · L58-L72 — def table_deleted(sender, table_id, table, user, **kwargs)
- tables_reordered · function · L76-L91 — def tables_reordered(sender, database, order, user, **kwargs): # Hashing all values here to not expose real ids of tables a user might not have # access to
- workspace_user_deleted · function · L95-L100 — def workspace_user_deleted(sender, workspace_user_id, workspace_user, user, **kwargs)
