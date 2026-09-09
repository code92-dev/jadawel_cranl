# backend/src/jadawel/contrib/database/data_sync/receivers.py

- rows_created_receiver · function · L19-L46 — def rows_created_receiver( sender, rows, before, user, table, model, send_realtime_update=True, send_webhook_events=True, m2m_change_tracker=None, skip_two_way_sync=False, **kwargs, )
- rows_updated_receiver · function · L50-L93 — def rows_updated_receiver( sender, rows, user, table, model, before_return, updated_field_ids, send_realtime_update=True, send_webhook_events=True, m2m_change_tracker=None, skip_two_way_sync=False, **kwargs, )
- rows_deleted_receiver · function · L97-L124 — def rows_deleted_receiver( sender, rows, user, table, model, before_return, send_realtime_update=True, send_webhook_events=True, m2m_change_tracker=None, skip_two_way_sync=False, **kwargs, )
