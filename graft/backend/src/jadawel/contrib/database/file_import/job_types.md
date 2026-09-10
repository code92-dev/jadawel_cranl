# backend/src/jadawel/contrib/database/file_import/job_types.py

- FileImportJobType · class · L49-L213 — class FileImportJobType(JobType)
- prepare_values · method · L95-L104 — def prepare_values(self, values, user)
- after_job_creation · method · L106-L117 — def after_job_creation(self, job, values)
- before_delete · method · L119-L128 — def before_delete(self, job)
- on_error · method · L130-L134 — def on_error(self, job, error)
- transaction_atomic_context · method · L136-L142 — def transaction_atomic_context(self, job: FileImportJob)
- cleanup_job · method · L144-L161 — def cleanup_job(self, job: FileImportJob, error_report: dict[str, Any])
- run · method · L163-L213 — def run(self, job, progress)
- after_commit · function · L204-L211 — def after_commit()
