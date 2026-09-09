# backend/src/jadawel/contrib/database/fields/webhook_event_types.py

- FieldEventType · class · L9-L26 — class FieldEventType(WebhookEventType)
- get_payload · method · L10-L14 — def get_payload(self, event_id, webhook, field, **kwargs)
- get_test_call_payload · method · L16-L23 — def get_test_call_payload(self, table, model, event_id, webhook)
- get_table_object · method · L25-L26 — def get_table_object(self, field, **kwargs)
- FieldCreatedEventType · class · L29-L31 — class FieldCreatedEventType(FieldEventType)
- FieldUpdatedEventType · class · L34-L36 — class FieldUpdatedEventType(FieldEventType)
- FieldDeletedEventType · class · L39-L58 — class FieldDeletedEventType(WebhookEventType)
- get_payload · method · L43-L46 — def get_payload(self, event_id, webhook, field_id, **kwargs)
- get_test_call_payload · method · L48-L55 — def get_test_call_payload(self, table, model, event_id, webhook)
- get_table_object · method · L57-L58 — def get_table_object(self, field, **kwargs)
