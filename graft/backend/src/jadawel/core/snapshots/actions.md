# backend/src/jadawel/core/snapshots/actions.py

- CreateSnapshotActionType · class · L18-L66 — class CreateSnapshotActionType(ActionType)
- Params · class · L33-L37 — class Params
- do · method · L40-L62 — def do(cls, user: AbstractUser, snapshot: Snapshot, progress: Progress)
- scope · method · L65-L66 — def scope(cls, workspace_id: int) -> ActionScopeStr
- RestoreSnapshotActionType · class · L69-L127 — class RestoreSnapshotActionType(ActionType)
- Params · class · L86-L92 — class Params
- do · method · L95-L123 — def do(cls, user: AbstractUser, snapshot: Snapshot, progress: Progress)
- scope · method · L126-L127 — def scope(cls, workspace_id: int) -> ActionScopeStr
- DeleteSnapshotActionType · class · L130-L189 — class DeleteSnapshotActionType(ActionType)
- Params · class · L145-L149 — class Params
- do · method · L152-L185 — def do(cls, user: AbstractUser, snapshot_id: int)
- scope · method · L188-L189 — def scope(cls, workspace_id: int) -> ActionScopeStr
