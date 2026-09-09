# backend/src/jadawel/api/applications/serializers.py

- ApplicationSerializer · class · L14-L34 — class ApplicationSerializer(serializers.ModelSerializer)
- Meta · class · L20-L30 — class Meta
- get_type · method · L33-L34 — def get_type(self, instance)
- PolymorphicApplicationResponseSerializer · class · L37-L40 — class PolymorphicApplicationResponseSerializer(PolymorphicSerializer)
- PublicPolymorphicApplicationResponseSerializer · class · L43-L47 — class PublicPolymorphicApplicationResponseSerializer( PolymorphicApplicationResponseSerializer )
- BaseApplicationCreatePolymorphicSerializer · class · L50-L58 — class BaseApplicationCreatePolymorphicSerializer(serializers.ModelSerializer)
- Meta · class · L56-L58 — class Meta
- PolymorphicApplicationCreateSerializer · class · L61-L63 — class PolymorphicApplicationCreateSerializer(PolymorphicRequestSerializer)
- BaseApplicationUpdatePolymorphicSerializer · class · L66-L69 — class BaseApplicationUpdatePolymorphicSerializer(serializers.ModelSerializer)
- Meta · class · L67-L69 — class Meta
- PolymorphicApplicationUpdateSerializer · class · L72-L74 — class PolymorphicApplicationUpdateSerializer(PolymorphicRequestSerializer)
- OrderApplicationsSerializer · class · L77-L81 — class OrderApplicationsSerializer(serializers.Serializer)
- InstallTemplateJobApplicationsSerializer · class · L84-L98 — class InstallTemplateJobApplicationsSerializer(serializers.JSONField)
- to_representation · method · L85-L98 — def to_representation(self, value)
