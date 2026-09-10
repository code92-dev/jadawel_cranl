# backend/src/jadawel/contrib/database/views/receivers.py

- _notify_table_data_updated · function · L28-L39 — def _notify_table_data_updated(table: Table, model: GeneratedTableModel | None = None)
- _notify_view_results_updated · function · L42-L50 — def _notify_view_results_updated(view: View)
- notify_rows_signals · function · L54-L61 — def notify_rows_signals(sender, rows, user, table, model, dependant_fields, **kwargs)
- notify_view_updated · function · L65-L66 — def notify_view_updated(sender, view, user, old_view, **kwargs)
- notify_view_filter_created_or_updated · function · L70-L71 — def notify_view_filter_created_or_updated(sender, view_filter, user, **kwargs)
- notify_view_filter_group_created_or_updated · function · L77-L80 — def notify_view_filter_group_created_or_updated( sender, view_filter_group, user, **kwargs )
- _notify_tables_of_fields_updated_or_deleted · function · L83-L88 — def _notify_tables_of_fields_updated_or_deleted(field, related_fields, user, **kwargs)
- notify_field_updated · function · L92-L93 — def notify_field_updated(sender, field, related_fields, user, **kwargs)
- notify_field_deleted · function · L97-L98 — def notify_field_deleted(sender, field_id, field, related_fields, user, **kwargs)
