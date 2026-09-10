# backend/src/jadawel/core/jobs/handler.py

- JobHandler · class · L19-L268 — class JobHandler
- cancel_job · method · L21-L40 — def cancel_job(cls, job: AnyJob) -> Job | None
- run · method · L43-L78 — def run(cls, job: AnyJob)
- progress_updated · function · L44-L63 — def progress_updated(percentage, state)
- get_job · method · L81-L107 — def get_job( cls, user: AbstractUser, job_id: int, job_model: Optional[Type[AnyJob]] = None, base_queryset: Optional[QuerySet] = None, ) -> Job
- get_jobs_for_user · method · L110-L154 — def get_jobs_for_user( cls, user: AbstractUser, filter_states: Optional[List[str]], filter_ids: Optional[List[int]], base_model: Optional[Type[AnyJob]] = None, type_filters: Optional[Dict[str, Any]] = None, ) -> QuerySet
- get_job_states_filter · function · L134-L141 — def get_job_states_filter(states)
- get_pending_or_running_jobs · method · L157-L171 — def get_pending_or_running_jobs( cls, job_type_name: str, ) -> QuerySet
- create_and_start_job · method · L173-L216 — def create_and_start_job( self, user: AbstractUser, job_type_name: str, sync=False, **kwargs ) -> Job
- call_async_job_safe · function · L201-L212 — def call_async_job_safe()
- clean_up_jobs · method · L218-L254 — def clean_up_jobs(self)
- delete_job · method · L257-L268 — def delete_job(cls, job: Type[Job])
