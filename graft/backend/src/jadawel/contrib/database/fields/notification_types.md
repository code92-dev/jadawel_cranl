# backend/src/jadawel/contrib/database/fields/notification_types.py

- CollaboratorAddedToRowNotificationData · class · L33-L41 — class CollaboratorAddedToRowNotificationData
- CollaboratorAddedToRowNotificationType · class · L44-L158 — class CollaboratorAddedToRowNotificationType( EmailNotificationTypeMixin, NotificationType )
- get_notification_title_for_email · method · L51-L61 — def get_notification_title_for_email(cls, notification, context)
- get_notification_description_for_email · method · L64-L65 — def get_notification_description_for_email(cls, notification, context)
- construct_notification · method · L68-L94 — def construct_notification( cls, sender: AbstractUser, row: "GeneratedTableModel", field: "Field" )
- _iter_field_row_and_collaborators_to_notify · method · L97-L125 — def _iter_field_row_and_collaborators_to_notify( cls, m2m_change_tracker: RowM2MChangeTracker, updated_rows: List["GeneratedTableModel"], ) -> List[Tuple["Field", "GeneratedTableModel", List[AbstractUser]]]: # The row provided by the iterator might not have all the updated values in # case of a bulk row update. This is because some fields require a returning # value after insert or update, but the `bulk_update` in the `create_rows` # method doesn't update these computed properties, so this row might have a # raw expression instead of the computed output. We're therefore replacing the # row from the updated set.
- create_notifications_grouped_by_user · method · L128-L158 — def create_notifications_grouped_by_user( cls, user: AbstractUser, m2m_change_tracker: RowM2MChangeTracker, rows: List["GeneratedTableModel"], )
- UserMentionInRichTextFieldNotificationData · class · L162-L170 — class UserMentionInRichTextFieldNotificationData
- UserMentionInRichTextFieldNotificationType · class · L174-L361 — class UserMentionInRichTextFieldNotificationType( EmailNotificationTypeMixin, NotificationType )
- get_notification_title_for_email · method · L181-L189 — def get_notification_title_for_email(cls, notification, context)
- get_notification_description_for_email · method · L192-L193 — def get_notification_description_for_email(cls, notification, context)
- construct_notification · method · L196-L222 — def construct_notification( cls, sender: AbstractUser, row: "GeneratedTableModel", field: "Field" )
- _iter_field_row_and_users_to_notify · method · L225-L330 — def _iter_field_row_and_users_to_notify( cls, rows: List["GeneratedTableModel"], updated_field_ids: Optional[List[int]] = None, ) -> Iterable[Tuple["Field", "GeneratedTableModel", List[AbstractUser]]]
- get_key · function · L258-L259 — def get_key(obj)
- create_notifications_grouped_by_user · method · L333-L361 — def create_notifications_grouped_by_user( cls, user: AbstractUser, rows: List["GeneratedTableModel"], updated_field_ids: Optional[List[int]] = None, )
- notify_users_when_rows_created · function · L365-L384 — def notify_users_when_rows_created( sender, rows, before, user, table, model, send_realtime_update=True, send_webhook_events=True, m2m_change_tracker=None, **kwargs, )
- notify_users_when_rows_updated · function · L388-L406 — def notify_users_when_rows_updated( sender, rows, user, table, model, before_return, updated_field_ids, m2m_change_tracker=None, **kwargs, )
