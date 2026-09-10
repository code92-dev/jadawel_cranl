# backend/src/jadawel/contrib/database/table/tasks.py

- unsubscribe_subject_from_tables_currently_subscribed_to · function · L25-L95 — def unsubscribe_subject_from_tables_currently_subscribed_to( subject_id: int, subject_type_name: str, scope_id: int, scope_type_name: str, workspace_id: int, permission_manager: PermissionManagerType = None, )
- unsubscribe_user_from_tables_when_removed_from_workspace · function · L102-L121 — def unsubscribe_user_from_tables_when_removed_from_workspace( self, user_id: int, workspace_id: int, )
- setup_created_by_and_last_modified_by_column · function · L129-L134 — def setup_created_by_and_last_modified_by_column(self, table_id: int)
- setup_m2m_field_indexes_if_not_exist · function · L142-L157 — def setup_m2m_field_indexes_if_not_exist(self, table_id: int)
- update_table_usage · function · L161-L166 — def update_table_usage(self, table_id: int, row_count: int = 0)
- create_tables_usage_for_new_database · function · L173-L176 — def create_tables_usage_for_new_database(self, database_id: int)
