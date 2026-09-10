# backend/src/jadawel/contrib/builder/domains/job_types.py

- PublishDomainJobType · class · L11-L38 — class PublishDomainJobType(JobType)
- transaction_atomic_context · method · L25-L33 — def transaction_atomic_context(self, job: PublishDomainJob): # It's possible for the Domain to be deleted prior to the execution of # this task (e.g. the export worker queue is down, and brought up again).
- run · method · L35-L38 — def run(self, job: PublishDomainJob, progress)
