# backend/src/jadawel/contrib/database/ws/views/rows/signals.py

- _send_rows_created_event_to_views · function · L24-L47 — def _send_rows_created_event_to_views( serialized_rows: List[Dict[Any, Any]], before: Optional[GeneratedTableModel], views: List[FilteredViewRows], user=None, )
- _send_rows_deleted_event_to_views · function · L51-L71 — def _send_rows_deleted_event_to_views( serialized_deleted_rows: List[Dict[Any, Any]], views: List[FilteredViewRows], user=None, )
- views_rows_created · function · L76-L100 — def views_rows_created( sender, rows, before, user, table, model, send_realtime_update=True, send_webhook_events=True, **kwargs, )
- views_before_rows_delete · function · L105-L114 — def views_before_rows_delete(sender, rows, user, table, model, **kwargs)
- views_rows_deleted · function · L119-L133 — def views_rows_deleted( sender, rows, user, table, model, before_return, send_realtime_update=True, **kwargs )
- views_before_rows_update · function · L138-L150 — def views_before_rows_update( sender, rows, user, table, model, updated_field_ids, **kwargs )
- views_rows_updated · function · L155-L271 — def views_rows_updated( sender, rows, user, table, model, before_return, updated_field_ids, send_realtime_update=True, **kwargs, )
- _send_created_updated_deleted_row_signals_to_views · function · L241-L269 — def _send_created_updated_deleted_row_signals_to_views()
