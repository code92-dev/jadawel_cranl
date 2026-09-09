# backend/src/jadawel/core/jobs/registries.py

- JobType · class · L32-L178 — class JobType( CustomFieldsInstanceMixin, ModelInstanceMixin, MapAPIExceptionsInstanceMixin, Instance, metaclass=jadawel_trace_methods(tracer, only="do"), )
- can_schedule_or_raise · method · L58-L77 — def can_schedule_or_raise(self, job: Job) -> None
- transaction_atomic_context · method · L79-L84 — def transaction_atomic_context(self, job: Job)
- prepare_values · method · L86-L101 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- after_job_creation · method · L103-L111 — def after_job_creation(self, job: AnyJob, values: Dict[str, Any])
- run · method · L113-L122 — def run(self, job: AnyJob, progress: Progress) -> Any
- before_delete · method · L124-L128 — def before_delete(self, job: AnyJob)
- on_error · method · L130-L137 — def on_error(self, job: AnyJob, error: Exception)
- request_serializer_class · method · L140-L150 — def request_serializer_class(self)
- response_serializer_class · method · L153-L164 — def response_serializer_class(self)
- get_filters_serializer · method · L166-L178 — def get_filters_serializer(self) -> Type[serializers.Serializer] | None
- JobTypeRegistry · class · L181-L193 — class JobTypeRegistry( CustomFieldsRegistryMixin, ModelRegistryMixin[Job, JobType], Registry[JobType], )
