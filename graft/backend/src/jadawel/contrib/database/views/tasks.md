# backend/src/jadawel/contrib/database/views/tasks.py

- get_auto_index_cache_key · function · L21-L22 — def get_auto_index_cache_key(view_id)
- update_view_index · function · L32-L55 — def update_view_index(view_id: int)
- _set_pending_view_index_update · function · L58-L63 — def _set_pending_view_index_update(view_id: int)
- _check_for_pending_view_index_updates · function · L70-L76 — def _check_for_pending_view_index_updates(view_id)
- _schedule_view_index_update · function · L79-L100 — def _schedule_view_index_update(view_id: int)
- schedule_view_index_update · function · L103-L115 — def schedule_view_index_update(view_id: int)
- periodic_check_for_views_with_time_sensitive_filters · function · L122-L130 — def periodic_check_for_views_with_time_sensitive_filters()
- setup_periodic_tasks · function · L134-L138 — def setup_periodic_tasks(sender, **kwargs)
