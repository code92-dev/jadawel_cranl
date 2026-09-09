# backend/src/jadawel/contrib/database/webhooks/notification_types.py

- DeactivatedWebhookData · class · L18-L31 — class DeactivatedWebhookData
- from_webhook · method · L25-L31 — def from_webhook(cls, webhook)
- WebhookDeactivatedNotificationType · class · L34-L68 — class WebhookDeactivatedNotificationType(EmailNotificationTypeMixin, NotificationType)
- notify_admins_in_workspace · method · L39-L53 — def notify_admins_in_workspace( cls, webhook: TableWebhook ) -> List[NotificationRecipient]
- get_notification_title_for_email · method · L56-L59 — def get_notification_title_for_email(cls, notification, context)
- get_notification_description_for_email · method · L62-L68 — def get_notification_description_for_email(cls, notification, context)
- WebhookPayloadTooLargeData · class · L72-L89 — class WebhookPayloadTooLargeData
- from_webhook · method · L81-L89 — def from_webhook(cls, webhook: TableWebhook, event_id: str)
- WebhookPayloadTooLargeNotificationType · class · L92-L134 — class WebhookPayloadTooLargeNotificationType( EmailNotificationTypeMixin, NotificationType )
- notify_admins_in_workspace · method · L99-L116 — def notify_admins_in_workspace( cls, webhook: TableWebhook, event_id: str ) -> List[NotificationRecipient]
- get_notification_title_for_email · method · L119-L122 — def get_notification_title_for_email(cls, notification, context)
- get_notification_description_for_email · method · L125-L134 — def get_notification_description_for_email(cls, notification, context)
