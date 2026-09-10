# backend/src/jadawel/contrib/database/webhooks/registries.py

- WebhookEventType · class · L16-L223 — class WebhookEventType(Instance)
- __init__ · method · L32-L39 — def __init__(self)
- get_test_call_payload · method · L41-L61 — def get_test_call_payload(self, table, model, event_id, webhook)
- get_payload · method · L63-L81 — def get_payload(self, event_id, webhook, **kwargs)
- get_table_object · method · L83-L101 — def get_table_object(self, **kwargs: dict) -> Table
- get_filters_for_webhooks_to_call · method · L103-L120 — def get_filters_for_webhooks_to_call(self, **kwargs: dict) -> Q
- listener · method · L122-L130 — def listener(self, **kwargs: dict)
- _paginate_payload · method · L132-L149 — def _paginate_payload( self, webhook: TableWebhook, event_id: str, payload: dict[str, any] ) -> tuple[dict, dict | None]
- paginate_payload · method · L151-L179 — def paginate_payload(self, webhook, event_id, payload) -> tuple[dict, dict | None]
- listener_after_commit · method · L181-L215 — def listener_after_commit(self, **kwargs)
- after_update · method · L217-L223 — def after_update(self, webhook_event: TableWebhookEvent)
- WebhookEventTypeRegistry · class · L226-L227 — class WebhookEventTypeRegistry(ModelRegistryMixin, Registry[WebhookEventType])
