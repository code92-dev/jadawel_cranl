# backend/tests/jadawel/core/notifications/utils.py

- custom_notification_types_registered · function · L12-L36 — def custom_notification_types_registered()
- ExcludedFromEmailTestNotification · class · L13-L14 — class ExcludedFromEmailTestNotification(NotificationType)
- TestNotification · class · L16-L27 — class TestNotification(EmailNotificationTypeMixin, NotificationType)
- get_notification_title_for_email · method · L20-L21 — def get_notification_title_for_email(cls, notification, context) -> str
- get_notification_description_for_email · method · L24-L27 — def get_notification_description_for_email( cls, notification, context ) -> Optional[str]
