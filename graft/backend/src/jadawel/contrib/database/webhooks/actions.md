# backend/src/jadawel/contrib/database/webhooks/actions.py

- CreateWebhookActionType · class · L17-L82 — class CreateWebhookActionType(ActionType)
- Params · class · L36-L46 — class Params
- do · method · L49-L78 — def do(cls, user: AbstractUser, table: Table, **kwargs) -> TableWebhook
- scope · method · L81-L82 — def scope(cls, table_id: int)
- DeleteWebhookActionType · class · L85-L146 — class DeleteWebhookActionType(ActionType)
- Params · class · L104-L114 — class Params
- do · method · L117-L142 — def do(cls, user: AbstractUser, webhook: TableWebhook, **kwargs)
- scope · method · L145-L146 — def scope(cls, table_id: int)
- UpdateWebhookActionType · class · L149-L222 — class UpdateWebhookActionType(ActionType)
- Params · class · L169-L182 — class Params
- do · method · L185-L218 — def do(cls, user: AbstractUser, webhook: TableWebhook, **data) -> TableWebhook
- scope · method · L221-L222 — def scope(cls, table_id: int)
