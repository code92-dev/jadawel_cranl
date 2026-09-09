# backend/src/jadawel/core/posthog.py

- get_posthog_client · function · L18-L33 — def get_posthog_client()
- capture_event · function · L36-L61 — def capture_event(distinct_id: str, event: str, properties: dict)
- capture_user_event · function · L64-L100 — def capture_user_event( user: AbstractUser, event: str, properties: dict, session: Optional[str] = None, workspace: Optional[Workspace] = None, )
- capture_event_action_done · function · L104-L125 — def capture_event_action_done( sender, user, action_type, action_params, action_timestamp, action_command_type, workspace, session, **kwargs, ): # Only capture do commands for now because the undo might make it more difficult # to do analytics on the data.
