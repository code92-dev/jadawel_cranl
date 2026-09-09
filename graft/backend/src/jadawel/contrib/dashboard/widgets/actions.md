# backend/src/jadawel/contrib/dashboard/widgets/actions.py

- CreateWidgetActionType · class · L17-L77 — class CreateWidgetActionType(UndoableActionType)
- Params · class · L27-L32 — class Params
- do · method · L35-L51 — def do( cls, user: AbstractUser, dashboard_id: int, widget_type: str, data: dict ) -> Widget
- scope · method · L54-L55 — def scope(cls, dashboard_id)
- undo · method · L58-L64 — def undo( cls, user: AbstractUser, params: Params, action_to_undo: Action, )
- redo · method · L67-L77 — def redo( cls, user: AbstractUser, params: Params, action_to_redo: Action, )
- UpdateWidgetActionType · class · L80-L148 — class UpdateWidgetActionType(UndoableActionType)
- Params · class · L90-L97 — class Params
- do · method · L100-L122 — def do( cls, user: AbstractUser, widget_id: int, widget_type: str, new_data: dict, ) -> Widget
- scope · method · L125-L126 — def scope(cls, dashboard_id)
- undo · method · L129-L137 — def undo( cls, user: AbstractUser, params: Params, action_to_undo: Action, )
- redo · method · L140-L148 — def redo( cls, user: AbstractUser, params: Params, action_to_redo: Action, )
- DeleteWidgetActionType · class · L151-L206 — class DeleteWidgetActionType(UndoableActionType)
- Params · class · L161-L165 — class Params
- do · method · L168-L180 — def do(cls, user: AbstractUser, widget_id: int) -> None
- scope · method · L183-L184 — def scope(cls, dashboard_id)
- undo · method · L187-L197 — def undo( cls, user: AbstractUser, params: Params, action_to_undo: Action, )
- redo · method · L200-L206 — def redo( cls, user: AbstractUser, params: Params, action_to_redo: Action, )
