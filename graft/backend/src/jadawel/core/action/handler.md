# backend/src/jadawel/core/action/handler.py

- scopes_to_q_filter · function · L27-L36 — def scopes_to_q_filter(scopes: List[ActionScopeStr])
- OneActionHasErrorAndCannotBeRedone · class · L39-L42 — class OneActionHasErrorAndCannotBeRedone(Exception)
- ActionHandler · class · L45-L356 — class ActionHandler(metaclass=jadawel_trace_methods(tracer))
- send_action_done_signal_for_actions · method · L52-L68 — def send_action_done_signal_for_actions( cls, user: AbstractUser, actions: List[Action], action_command_type: ActionCommandType, **kwargs, ) -> None
- _undo_action · method · L71-L90 — def _undo_action( cls, user: AbstractUser, action: Action, undone_at: datetime ) -> None
- undo · method · L94-L151 — def undo( cls, user: AbstractUser, scopes: List[ActionScopeStr], session: str ) -> List[Action]: # Un-set the web_socket_id so the user doing this undo will receive any # events triggered by the action.
- _redo_action · method · L154-L172 — def _redo_action(cls, user: AbstractUser, action: Action) -> None: # noinspection PyBroadException
- redo · method · L176-L265 — def redo( cls, user: AbstractUser, scopes: List[ActionScopeStr], session: str ) -> List[Action]: # Un-set the web_socket_id so the user doing this redo will receive any # events triggered by the action.
- clean_up_old_undoable_actions · method · L268-L309 — def clean_up_old_undoable_actions(cls)
- _cleanup_actions_with_custom_cleanup_logic · method · L312-L356 — def _cleanup_actions_with_custom_cleanup_logic( cls, cutoff: datetime, types_with_custom_clean_up: Set[str] ) -> Tuple[int, Optional[Exception]]
