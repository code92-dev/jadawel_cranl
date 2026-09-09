# backend/src/jadawel/core/notifications/receivers.py

- notify_notification_created · function · L20-L47 — def notify_notification_created( sender, notification: Notification, notification_recipients: List[NotificationRecipient], **kwargs, )
- notify_notification_marked_as_read · function · L51-L74 — def notify_notification_marked_as_read( sender, notification: Notification, notification_recipient: NotificationRecipient, user: AbstractUser, ignore_web_socket_id=None, **kwargs, )
- notify_all_notifications_marked_as_read · function · L78-L89 — def notify_all_notifications_marked_as_read(sender, user: AbstractUser, **kwargs)
- notify_all_notifications_cleared · function · L93-L104 — def notify_all_notifications_cleared(sender, user: AbstractUser, **kwargs)
