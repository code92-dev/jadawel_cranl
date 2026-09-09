# backend/src/jadawel/contrib/database/ws/views/rows/handler.py

- ViewRealtimeRowsHandler · class · L12-L85 — class ViewRealtimeRowsHandler
- _is_name · method · L13-L14 — def _is_name(self, name)
- get_views_row_checker · method · L16-L70 — def get_views_row_checker( self, table: Table, model: GeneratedTableModel, only_include_views_which_want_realtime_events: bool, updated_field_ids: Optional[List[int]] = None, ) -> FilteredViewRowChecker
- broadcast_to_types · method · L72-L85 — def broadcast_to_types(self, view: View, payload: Dict, user=None)
