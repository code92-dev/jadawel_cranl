# backend/src/jadawel/core/job_types.py

- DuplicateApplicationJobType · class · L76-L142 — class DuplicateApplicationJobType(JobType)
- transaction_atomic_context · method · L109-L116 — def transaction_atomic_context(self, job: "DuplicateApplicationJob")
- prepare_values · method · L118-L125 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- run · method · L127-L142 — def run(self, job: DuplicateApplicationJob, progress: Progress) -> Application
- InstallTemplateJobType · class · L145-L220 — class InstallTemplateJobType(JobType)
- prepare_values · method · L186-L206 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- run · method · L208-L220 — def run(self, job: InstallTemplateJob, progress: Progress) -> List[Application]
- _empty_transaction_context · function · L224-L233 — def _empty_transaction_context()
- ExportApplicationsJobType · class · L236-L362 — class ExportApplicationsJobType(JobType)
- transaction_atomic_context · method · L277-L284 — def transaction_atomic_context(self, job: "DuplicateApplicationJob")
- fetch_applications · method · L286-L327 — def fetch_applications(self, user, workspace, application_ids)
- prepare_values · method · L329-L343 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- run · method · L345-L362 — def run(self, job: ExportApplicationsJob, progress: Progress)
- ImportApplicationsJobType · class · L365-L464 — class ImportApplicationsJobType(JobType)
- transaction_atomic_context · method · L412-L418 — def transaction_atomic_context(self, job: "DuplicateApplicationJob")
- prepare_values · method · L420-L443 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- run · method · L445-L464 — def run(self, job: ImportApplicationsJob, progress: Progress)
