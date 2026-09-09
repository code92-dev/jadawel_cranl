# backend/src/jadawel/contrib/automation/workflows/job_types.py

- DuplicateAutomationWorkflowJobType · class · L32-L83 — class DuplicateAutomationWorkflowJobType(JobType)
- transaction_atomic_context · method · L54-L55 — def transaction_atomic_context(self, job: "DuplicateAutomationWorkflowJobType")
- prepare_values · method · L57-L69 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- run · method · L71-L83 — def run(self, job, progress)
- PublishAutomationWorkflowJobType · class · L86-L116 — class PublishAutomationWorkflowJobType(JobType)
- transaction_atomic_context · method · L96-L109 — def transaction_atomic_context(self, job: PublishAutomationWorkflowJob): # It's possible for the AutomationWorkflow to be deleted prior to # the execution of this task (e.g. the export worker queue is down, # and brought up again).
- run · method · L111-L116 — def run(self, job: PublishAutomationWorkflowJob, progress)
