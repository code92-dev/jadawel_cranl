# backend/src/jadawel/api/jobs/serializers.py

- JobSerializer · class · L26-L56 — class JobSerializer(serializers.ModelSerializer)
- Meta · class · L39-L52 — class Meta
- get_type · method · L55-L56 — def get_type(self, instance)
- CreateJobSerializer · class · L59-L67 — class CreateJobSerializer(serializers.Serializer)
- Meta · class · L65-L67 — class Meta
- JobTypeFiltersSerializer · class · L70-L80 — class JobTypeFiltersSerializer(serializers.Serializer)
- ListJobQuerySerializer · class · L83-L162 — class ListJobQuerySerializer(serializers.Serializer)
- validate_states · method · L96-L108 — def validate_states(self, value)
- validate_job_ids · method · L110-L123 — def validate_job_ids(self, value)
- validate · method · L125-L162 — def validate(self, attrs)
- ListJobQuerySerializerExtension · class · L165-L215 — class ListJobQuerySerializerExtension(OpenApiSerializerExtension)
- map_serializer · method · L175-L215 — def map_serializer(self, auto_schema, direction)
