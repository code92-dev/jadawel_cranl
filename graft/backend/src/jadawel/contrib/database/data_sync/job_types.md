# backend/src/jadawel/contrib/database/data_sync/job_types.py

- validation_error_to_human_readable_string · function · L33-L34 — def validation_error_to_human_readable_string(e)
- SyncDataSyncTableJobType · class · L37-L109 — class SyncDataSyncTableJobType(JobType)
- transaction_atomic_context · method · L63-L68 — def transaction_atomic_context(self, job: "SyncDataSyncTableJob"): # If the job doesn't exist, the job won't be executed, so we can start a normal # transaction.
- prepare_values · method · L70-L81 — def prepare_values(self, values, user)
- run · method · L83-L109 — def run(self, job, progress): # Don't do anything if the data sync and/or table has been deleted because then # there is nothing to update anymore.
