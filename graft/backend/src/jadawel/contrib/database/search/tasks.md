# backend/src/jadawel/contrib/database/search/tasks.py

- _get_singleton_autoreschedule_flag · function · L20-L21 — def _get_singleton_autoreschedule_flag(table_id: int) -> SingletonAutoRescheduleFlag
- schedule_update_search_data · function · L28-L76 — def schedule_update_search_data( table_id: int, field_ids: Optional[List[int]] = None, row_ids: Optional[List[int]] = None, )
- update_search_data · function · L89-L135 — def update_search_data(table_id: int)
- periodic_check_pending_search_data · function · L147-L186 — def periodic_check_pending_search_data()
- setup_periodic_tasks · function · L190-L194 — def setup_periodic_tasks(sender, **kwargs)
