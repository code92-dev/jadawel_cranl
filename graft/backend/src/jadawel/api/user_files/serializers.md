# backend/src/jadawel/api/user_files/serializers.py

- UserFileUploadViaURLRequestSerializer · class · L12-L13 — class UserFileUploadViaURLRequestSerializer(serializers.Serializer)
- UserFileURLAndThumbnailsSerializerMixin · class · L16-L48 — class UserFileURLAndThumbnailsSerializerMixin(serializers.Serializer)
- get_instance_attr · method · L20-L21 — def get_instance_attr(self, instance, name)
- get_url · method · L24-L29 — def get_url(self, instance)
- get_thumbnails · method · L32-L48 — def get_thumbnails(self, instance)
- UserFileSerializer · class · L51-L73 — class UserFileSerializer( UserFileURLAndThumbnailsSerializerMixin, serializers.ModelSerializer )
- Meta · class · L56-L69 — class Meta
- get_name · method · L72-L73 — def get_name(self, instance)
- UserFileField · class · L77-L125 — class UserFileField(serializers.Field)
- __init__ · method · L103-L106 — def __init__(self, *args, **kwargs)
- to_internal_value · method · L108-L120 — def to_internal_value(self, data)
- to_representation · method · L122-L125 — def to_representation(self, value)
