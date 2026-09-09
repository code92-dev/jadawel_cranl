# backend/src/jadawel/test_utils/fixtures/job.py

- TestException · class · L17-L17 — class TestException(Exception)
- TmpJobType1FiltersSerializer · class · L20-L27 — class TmpJobType1FiltersSerializer(serializers.Serializer)
- TmpJobType1 · class · L30-L68 — class TmpJobType1(JobType)
- prepare_values · method · L59-L60 — def prepare_values(self, values, user)
- run · method · L62-L63 — def run(self, job, progress)
- get_filters_serializer · method · L65-L68 — def get_filters_serializer(self) -> Type[serializers.Serializer] | None
- TmpJobType2 · class · L71-L79 — class TmpJobType2(JobType)
- run · method · L78-L79 — def run(self, job, progress)
- TmpJobType3 · class · L82-L115 — class TmpJobType3(JobType)
- prepare_values · method · L111-L112 — def prepare_values(self, values, user)
- run · method · L114-L115 — def run(self, job, progress)
- JobFixtures · class · L118-L135 — class JobFixtures
- register_temp_job_types · method · L119-L125 — def register_temp_job_types(self)
- create_fake_job · method · L127-L135 — def create_fake_job(self, **kwargs)
