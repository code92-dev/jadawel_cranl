# backend/src/jadawel/core/snapshots/handler.py

- SnapshotHandler · class · L43-L486 — class SnapshotHandler
- _count · method · L44-L56 — def _count(self, workspace: Workspace) -> int
- _check_is_in_use · method · L58-L79 — def _check_is_in_use(self, snapshot: Snapshot) -> None
- list · method · L81-L121 — def list(self, application_id: int, performed_by: AbstractUser) -> QuerySet
- start_create_job · method · L123-L160 — def start_create_job( self, application_id: int, performed_by: AbstractUser, name: str )
- create · method · L162-L215 — def create(self, application_id, performed_by, name)
- start_restore_job · method · L217-L277 — def start_restore_job( self, snapshot_id: int, performed_by: AbstractUser, ) -> Job
- _schedule_deletion · method · L279-L283 — def _schedule_deletion(self, snapshot: Snapshot)
- delete · method · L285-L333 — def delete(self, snapshot_id: int, performed_by: AbstractUser) -> None
- delete_by_application · method · L335-L347 — def delete_by_application(self, application: Application) -> None
- delete_expired · method · L349-L362 — def delete_expired(self) -> None
- perform_create · method · L364-L427 — def perform_create(self, snapshot: Snapshot, progress: Progress) -> None
- perform_restore · method · L429-L486 — def perform_restore(self, snapshot: Snapshot, progress: Progress) -> Application
