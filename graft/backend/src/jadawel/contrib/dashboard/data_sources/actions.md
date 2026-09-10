# backend/src/jadawel/contrib/dashboard/data_sources/actions.py

- UpdateDashboardDataSourceActionType · class · L16-L100 — class UpdateDashboardDataSourceActionType(UndoableActionType)
- Params · class · L26-L33 — class Params
- do · method · L36-L66 — def do( cls, user: AbstractUser, data_source_id: int, service_type, new_data: dict, ) -> DashboardDataSource
- scope · method · L69-L70 — def scope(cls, dashboard_id)
- undo · method · L73-L85 — def undo( cls, user: AbstractUser, params: Params, action_to_undo: Action, )
- redo · method · L88-L100 — def redo( cls, user: AbstractUser, params: Params, action_to_redo: Action, )
