# backend/src/jadawel/core/notifications/service.py

- NotificationService · class · L20-L119 — class NotificationService
- get_workspace_if_has_permissions_or_raise · method · L22-L30 — def get_workspace_if_has_permissions_or_raise( cls, user: AbstractUser, workspace_id: int, permission_type: Type[OperationType] )
- list_notifications · method · L33-L38 — def list_notifications(cls, user, workspace_id: int)
- get_notification · method · L41-L67 — def get_notification( cls, user: AbstractUser, workspace_id: int, notification_id: int, ) -> NotificationRecipient
- mark_notification_as_read · method · L70-L82 — def mark_notification_as_read( cls, user: AbstractUser, workspace_id: int, notification_id: int, read: bool = True, ) -> NotificationRecipient
- mark_all_notifications_as_read · method · L85-L99 — def mark_all_notifications_as_read(cls, user: AbstractUser, workspace_id: int)
- clear_all_notifications · method · L102-L119 — def clear_all_notifications( cls, user: AbstractUser, workspace_id: int, )
