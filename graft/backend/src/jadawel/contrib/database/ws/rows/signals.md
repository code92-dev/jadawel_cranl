# backend/src/jadawel/contrib/database/ws/rows/signals.py

- serialize_rows_values · function · L22-L36 — def serialize_rows_values( sender, rows, user, table, model, updated_field_ids, serialize_only_updated_fields: bool = False, **kwargs, )
- rows_created · function · L40-L70 — def rows_created( sender, rows, before, user, table, model, send_realtime_update=True, send_webhook_events=True, **kwargs, )
- rows_updated · function · L74-L117 — def rows_updated( sender, rows, user, table, model, before_return, updated_field_ids, send_realtime_update=True, serialize_only_updated_fields: bool = False, **kwargs, )
- rows_ai_values_generation_error · function · L121-L137 — def rows_ai_values_generation_error( sender, user, rows, field, table, error_message, **kwargs )
- before_rows_delete · function · L141-L144 — def before_rows_delete(sender, rows, user, table, model, **kwargs)
- rows_deleted · function · L148-L164 — def rows_deleted( sender, rows, user, table, model, before_return, send_realtime_update=True, **kwargs )
- row_orders_recalculated · function · L168-L175 — def row_orders_recalculated(sender, table, **kwargs)
- rows_history_updated · function · L179-L208 — def rows_history_updated( sender, table_id, row_history_entries: "list[RowHistory]", **kwargs, )
- send_rows · function · L187-L206 — def send_rows()
- RealtimeRowMessages · class · L211-L268 — class RealtimeRowMessages
- rows_deleted · method · L218-L226 — def rows_deleted( table_id: int, serialized_rows: List[Dict[str, Any]] ) -> Dict[str, Any]
- rows_created · method · L229-L241 — def rows_created( table_id: int, serialized_rows: List[Dict[str, Any]], metadata: Dict[str, Any], before: Optional[GeneratedTableModel], ) -> Dict[str, Any]
- rows_updated · method · L244-L261 — def rows_updated( table_id: int, serialized_rows_before_update: List[Dict[str, Any]], serialized_rows: List[Dict[str, Any]], metadata: Dict[int, Dict[str, Any]], updated_field_ids: List[int], ) -> Dict[str, Any]
- row_orders_recalculated · method · L264-L268 — def row_orders_recalculated(table_id: int) -> Dict[str, Any]
