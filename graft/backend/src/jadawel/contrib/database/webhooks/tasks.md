# backend/src/jadawel/contrib/database/webhooks/tasks.py

- get_queue · function · L19-L26 — def get_queue(webhook_id)
- enqueue_webhook_task · function · L29-L37 — def enqueue_webhook_task(webhook_id, event_id, args, kwargs)
- clear_webhook_queue · function · L40-L42 — def clear_webhook_queue(webhook_id)
- schedule_next_task_in_queue · function · L45-L48 — def schedule_next_task_in_queue(webhook_id)
- call_webhook · function · L57-L175 — def call_webhook( self, webhook_id: int, event_id: str, event_type: str, method: str, url: str, headers: dict, payload: dict, retries: int = 0, **kwargs: dict, )
- make_request_and_save_result · function · L178-L257 — def make_request_and_save_result( webhook, event_id, event_type, method, url, headers, payload )
