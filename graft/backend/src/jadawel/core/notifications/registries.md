# backend/src/jadawel/core/notifications/registries.py

- NotificationType · class · L22-L36 — class NotificationType(MapAPIExceptionsInstanceMixin, Instance)
- get_web_frontend_url · method · L26-L36 — def get_web_frontend_url(self, notification: Notification) -> Optional[str]
- EmailNotificationTypeMixin · class · L39-L78 — class EmailNotificationTypeMixin(metaclass=ABCMeta)
- get_notification_title_for_email · method · L55-L58 — def get_notification_title_for_email(cls, notification, context) -> str
- get_notification_description_for_email · method · L62-L68 — def get_notification_description_for_email( cls, notification, context ) -> Optional[str]
- get_web_frontend_url · method · L70-L78 — def get_web_frontend_url(self, notification)
- CliNotificationTypeMixin · class · L81-L88 — class CliNotificationTypeMixin(metaclass=ABCMeta)
- prompt_for_args_in_cli_and_create_notification · method · L84-L88 — def prompt_for_args_in_cli_and_create_notification(cls)
- NotificationTypeDoesNotExist · class · L91-L92 — class NotificationTypeDoesNotExist(InstanceTypeDoesNotExist)
- NotificationTypeAlreadyRegistered · class · L95-L96 — class NotificationTypeAlreadyRegistered(InstanceTypeAlreadyRegistered)
- NotificationTypeRegistry · class · L99-L111 — class NotificationTypeRegistry( CustomFieldsRegistryMixin, ModelRegistryMixin[Notification, NotificationType], Registry[NotificationType], )
