# backend/src/jadawel/contrib/database/webhooks/handler.py

- WebhookHandler · class · L46-L550 — class WebhookHandler
- find_webhooks_to_call · method · L47-L70 — def find_webhooks_to_call( self, webhook_event_type: "WebhookEventType", **webhook_event_type_kwargs ) -> QuerySet[TableWebhook]
- get_table_webhook · method · L72-L99 — def get_table_webhook( self, user: DjangoUser, webhook_id: int, base_queryset: Optional[QuerySet] = None, ) -> TableWebhook
- _get_table_webhook · method · L101-L128 — def _get_table_webhook( self, webhook_id: int, base_queryset: Optional[QuerySet] = None ) -> TableWebhook
- get_all_table_webhooks · method · L130-L149 — def get_all_table_webhooks(self, user: any, table: Table) -> QuerySet
- _update_webhook_event_config · method · L151-L198 — def _update_webhook_event_config( self, webhook: TableWebhook, event_config: List[EventConfigItem], webhook_events: Optional[List[TableWebhookEvent]] = None, )
- create_table_webhook · method · L200-L268 — def create_table_webhook( self, user: DjangoUser, table: Table, events: Optional[List[str]] = None, event_config: Optional[List[EventConfigItem]] = None, headers: Optional[dict] = None, **kwargs: dict, ) -> TableWebhook
- update_table_webhook · method · L270-L387 — def update_table_webhook( self, user: DjangoUser, webhook: TableWebhook, events: Optional[List[str]] = None, event_config: Optional[List[EventConfigItem]] = None, headers: Optional[List[dict]] = None, **kwargs: dict, ) -> TableWebhook
- delete_table_webhook · method · L389-L405 — def delete_table_webhook(self, user: DjangoUser, webhook: TableWebhook)
- make_request · method · L407-L440 — def make_request( self, method: str, url: str, headers: dict, payload: dict ) -> Response
- get_headers · method · L442-L449 — def get_headers(self, event_type: str, event_id: str)
- trigger_test_call · method · L451-L502 — def trigger_test_call( self, user: DjangoUser, table: Table, event_type: str, headers: Optional[dict] = None, **kwargs: dict, )
- format_request · method · L504-L513 — def format_request(self, request: PreparedRequest) -> str
- format_response · method · L515-L531 — def format_response(self, response: Response) -> str
- clean_webhook_calls · method · L533-L550 — def clean_webhook_calls(self, webhook: TableWebhook)
