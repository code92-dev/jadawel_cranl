# backend/src/jadawel/contrib/database/views/notification_types.py

- FormSubmittedNotificationData · class · L23-L30 — class FormSubmittedNotificationData
- FormSubmittedNotificationType · class · L33-L109 — class FormSubmittedNotificationType(EmailNotificationTypeMixin, NotificationType)
- create_form_submitted_notification · method · L38-L82 — def create_form_submitted_notification( cls, form, row, values, users_to_notify, sender=None )
- get_notification_title_for_email · method · L85-L89 — def get_notification_title_for_email(cls, notification, context)
- get_notification_description_for_email · method · L92-L109 — def get_notification_description_for_email(cls, notification, context)
- create_form_submitted_notification · function · L113-L128 — def create_form_submitted_notification(sender, form, row, values, user, **kwargs)
