# backend/tests/jadawel/api/jobs/test_jobs_views.py

- test_create_job · function · L19-L121 — def test_create_job(mock_run_async, data_fixture, api_client)
- test_list_jobs · function · L125-L224 — def test_list_jobs(data_fixture, api_client)
- test_list_jobs_with_type_specific_filters · function · L229-L261 — def test_list_jobs_with_type_specific_filters(mock_run_async, data_fixture, api_client)
- test_get_job · function · L265-L330 — def test_get_job(data_fixture, api_client)
- test_cancel_job_running · function · L335-L418 — def test_cancel_job_running( data_fixture, api_client, test_thread, mutable_job_type_registry ): # marker that the job started
- IdlingJobType · class · L349-L360 — class IdlingJobType(JobType)
- run · method · L354-L360 — def run(self, job, progress)
- test_cancel_job_pending · function · L423-L491 — def test_cancel_job_pending( data_fixture, api_client, test_thread, mutable_job_type_registry ): # marker that the job started
- IdlingJobType · class · L435-L445 — class IdlingJobType(JobType)
- run · method · L440-L445 — def run(self, job, progress)
- test_cancel_job_finished · function · L496-L565 — def test_cancel_job_finished( data_fixture, api_client, test_thread, mutable_job_type_registry ): # marker that the job started
- IdlingJobType · class · L508-L518 — class IdlingJobType(JobType)
- run · method · L513-L518 — def run(self, job, progress)
