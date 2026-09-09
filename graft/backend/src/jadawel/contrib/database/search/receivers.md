# backend/src/jadawel/contrib/database/search/receivers.py

- handle_permanently_deleted_workspace · function · L11-L19 — def handle_permanently_deleted_workspace( sender, trash_item_id, trash_item: "Workspace", parent_id, *args, **kwargs )
- handle_permanently_deleted_table · function · L23-L38 — def handle_permanently_deleted_table( sender, trash_item_id, trash_item, parent_id, *args, **kwargs )
- handle_permanently_deleted_field · function · L42-L56 — def handle_permanently_deleted_field( sender, trash_item_id, trash_item, parent_id, *args, **kwargs )
- handle_permanently_deleted_row · function · L60-L73 — def handle_permanently_deleted_row( sender, trash_item_id, trash_item, parent_id, *args, **kwargs )
- handle_permanently_deleted_rows · function · L77-L94 — def handle_permanently_deleted_rows( sender, trash_item_id, trash_item, parent_id, *args, **kwargs )
- view_loaded_schedule_update_search_data · function · L98-L125 — def view_loaded_schedule_update_search_data( sender, table: "Table", table_model: type["GeneratedTableModel"], **kwargs, )
