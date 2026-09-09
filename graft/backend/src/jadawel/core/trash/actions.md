# backend/src/jadawel/core/trash/actions.py

- EmptyTrashActionType · class · L18-L89 — class EmptyTrashActionType(ActionType)
- Params · class · L33-L37 — class Params
- _get_application · method · L40-L44 — def _get_application(cls, application_id: int)
- _get_workspace · method · L47-L51 — def _get_workspace(cls, workspace_id: int)
- do · method · L54-L73 — def do( cls, user: AbstractUser, workspace_id: int, application_id: Optional[int] = None )
- scope · method · L76-L77 — def scope(cls, workspace_id: int)
- get_long_description · method · L80-L89 — def get_long_description(cls, params_dict: Dict[str, Any], *args, **kwargs) -> str
- RestoreFromTrashActionType · class · L92-L150 — class RestoreFromTrashActionType(ActionType)
- Params · class · L105-L110 — class Params
- do · method · L113-L146 — def do( cls, user: AbstractUser, trash_item_type: str, trash_item_id: int, parent_trash_item_id: Optional[int] = None, )
- scope · method · L149-L150 — def scope(cls, workspace_id: int)
