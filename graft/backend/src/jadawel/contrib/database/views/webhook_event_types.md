# backend/src/jadawel/contrib/database/views/webhook_event_types.py

- ViewEventType · class · L11-L28 — class ViewEventType(WebhookEventType)
- get_payload · method · L12-L18 — def get_payload(self, event_id, webhook, view, user, **kwargs)
- get_test_call_payload · method · L20-L25 — def get_test_call_payload(self, table, model, event_id, webhook)
- get_table_object · method · L27-L28 — def get_table_object(self, view, **kwargs)
- ViewCreatedEventType · class · L31-L33 — class ViewCreatedEventType(ViewEventType)
- ViewUpdatedEventType · class · L36-L38 — class ViewUpdatedEventType(ViewEventType)
- ViewDeletedEventType · class · L41-L60 — class ViewDeletedEventType(WebhookEventType)
- get_payload · method · L45-L48 — def get_payload(self, event_id, webhook, view_id, **kwargs)
- get_test_call_payload · method · L50-L57 — def get_test_call_payload(self, table, model, event_id, webhook)
- get_table_object · method · L59-L60 — def get_table_object(self, view, **kwargs)
