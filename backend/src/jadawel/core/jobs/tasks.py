from datetime import timedelta

from django.conf import settings

from loguru import logger

from jadawel.config.celery import app
from jadawel.core.jobs.exceptions import JobCancelled
from jadawel.core.jobs.registries import job_type_registry
from jadawel.core.sentry import setup_user_in_sentry
from jadawel.core.telemetry.utils import setup_user_in_baggage_and_spans


@app.task(
    name="jadawel.core.jobs.tasks.run_async_job",
    bind=True,
    queue="export",
    soft_time_limit=settings.JADAWEL_JOB_SOFT_TIME_LIMIT,
)
def run_async_job(self, job_id: int):
    """Run the job task asynchronously"""

    from celery.exceptions import SoftTimeLimitExceeded

    from jadawel.core.jobs.handler import JobHandler
    from jadawel.core.jobs.models import Job

    job = Job.objects.select_related("user", "content_type").get(id=job_id).specific
    if job.cancelled:
        return  # Job cancelled before it started. No need to run it.

    with setup_user_in_baggage_and_spans(job.user):
        setup_user_in_sentry(job.user)

        job_type = job_type_registry.get_by_model(job)
        job.set_state_started()
        job.save()

        try:
            with job_type.transaction_atomic_context(job):
                JobHandler.run(job)

            job.set_state_finished()
            job.save()
        except JobCancelled:
            # It shouldn't be necessary because the JobHandler shouldn't call
            # job.save(), but this guarantees that the job is in the cancelled state
            # at the end.
            job.set_state_cancelled()
            job.save()
        except BaseException as e:
            # BaseException allows catching SystemExit exceptions and all other possible
            # exceptions to set the job state in a failed state.
            error = f"Something went wrong during the {job_type.type} job execution."

            exception_mapping = {
                SoftTimeLimitExceeded: f"The {job_type.type} job took too long and was "
                "timed out."
            }
            exception_mapping.update(job_type.job_exceptions_map)

            should_raise = True
            for exception, error_message in exception_mapping.items():
                if isinstance(e, exception):
                    if callable(error_message):
                        error_message = error_message(e)
                    error = error_message.format(e=e)
                    should_raise = False
                    break

            job.set_state_failed(str(e), error)
            job.save()

            try:
                job_type.on_error(job, e)
            except Exception:
                logger.exception(
                    f"The on_error hook of the {job_type.type} job {job.id} failed."
                )

            if should_raise:
                raise
        finally:
            # Delete the import job cached entry because the transaction has been
            # committed and the Job entry now contains the latest data.
            job.clear_job_cache()


# noinspection PyUnusedLocal
@app.task(
    name="jadawel.core.jobs.tasks.clean_up_jobs",
    bind=True,
)
def clean_up_jobs(self):
    """
    Execute job cleanup for each job types if they need to cleanup something like files
    or old jobs.
    """

    from jadawel.core.jobs.handler import JobHandler

    JobHandler().clean_up_jobs()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.JADAWEL_JOB_CLEANUP_INTERVAL_MINUTES),
        clean_up_jobs.s(),
    )
