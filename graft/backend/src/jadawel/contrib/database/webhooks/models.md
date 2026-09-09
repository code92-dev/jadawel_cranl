# backend/src/jadawel/contrib/database/webhooks/models.py

- WebhookRequestMethods · class · L16-L21 — class WebhookRequestMethods(models.TextChoices)
- TableWebhook · class · L24-L77 — class TableWebhook(CreatedAndUpdatedOnMixin, models.Model)
- header_dict · method · L61-L62 — def header_dict(self)
- batch_limit · method · L65-L74 — def batch_limit(self) -> int
- Meta · class · L76-L77 — class Meta
- TableWebhookEvent · class · L80-L99 — class TableWebhookEvent(CreatedAndUpdatedOnMixin, models.Model)
- get_type · method · L93-L96 — def get_type(self)
- Meta · class · L98-L99 — class Meta
- TableWebhookHeader · class · L102-L110 — class TableWebhookHeader(models.Model)
- Meta · class · L109-L110 — class Meta
- TableWebhookCall · class · L113-L147 — class TableWebhookCall(models.Model)
- Meta · class · L145-L147 — class Meta
