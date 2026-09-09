# backend/src/jadawel/core/snapshots/job_types.py

- CreateSnapshotJobType · class · L19-L62 — class CreateSnapshotJobType(JobType)
- serializer_field_overrides · method · L37-L42 — def serializer_field_overrides(self)
- transaction_atomic_context · method · L44-L49 — def transaction_atomic_context(self, job: CreateSnapshotJob)
- run · method · L51-L56 — def run(self, job: CreateSnapshotJob, progress)
- before_delete · method · L58-L62 — def before_delete(self, job): # Delete the dangling snapshot if it didn't finish correctly but the snapshot is # still there.
- RestoreSnapshotJobType · class · L65-L90 — class RestoreSnapshotJobType(JobType)
- serializer_field_overrides · method · L78-L83 — def serializer_field_overrides(self)
- run · method · L85-L90 — def run(self, job: RestoreSnapshotJob, progress)
