# backend/src/jadawel/contrib/database/fields/tasks.py

- filter_distinct_workspace_ids_per_fields · function · L28-L45 — def filter_distinct_workspace_ids_per_fields( queryset: QuerySet, workspace_id: Optional[int] = None ) -> QuerySet
- run_periodic_fields_updates · function · L54-L84 — def run_periodic_fields_updates( self, workspace_id: Optional[int] = None, update_now: bool = True )
- _run_periodic_field_type_update_per_workspace · function · L88-L139 — def _run_periodic_field_type_update_per_workspace( field_type_instance: Type[FieldType], workspace: Workspace, update_now: bool = True )
- notify_table_views_updates · function · L145-L170 — def notify_table_views_updates(self, table_ids)
- delete_mentions_marked_for_deletion · function · L177-L183 — def delete_mentions_marked_for_deletion(self)
- setup_periodic_tasks · function · L187-L194 — def setup_periodic_tasks(sender, **kwargs)
