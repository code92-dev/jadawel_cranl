# backend/src/jadawel/contrib/database/rows/history.py

- RowHistoryHandler · class · L28-L100 — class RowHistoryHandler
- record_history_from_rows_action · method · L31-L50 — def record_history_from_rows_action( cls, user: AnyUser, action: ActionData, row_history_provider: RowHistoryProviderType, )
- list_row_history · method · L54-L71 — def list_row_history( cls, workspace: Workspace, table_id: int, row_id: int ) -> QuerySet[RowHistory]
- delete_entries_older_than · method · L74-L100 — def delete_entries_older_than(cls, cutoff: datetime, batch_size: int = 20_000)
- on_action_done_update_row_history · function · L104-L132 — def on_action_done_update_row_history( sender, user, action_type, action_params, action_timestamp, action_command_type, workspace, action_uuid, **kwargs, )
