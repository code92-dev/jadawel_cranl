# backend/src/jadawel/contrib/database/api/tokens/serializers.py

- TokenPermissionsField · class · L11-L169 — class TokenPermissionsField(serializers.Field)
- __init__ · method · L24-L26 — def __init__(self, **kwargs)
- to_internal_value · method · L28-L119 — def to_internal_value(self, data)
- to_representation · method · L121-L169 — def to_representation(self, value)
- TokenPermissionsFieldFix · class · L172-L178 — class TokenPermissionsFieldFix(OpenApiSerializerFieldExtension)
- map_serializer_field · method · L177-L178 — def map_serializer_field(self, auto_schema, direction)
- TokenSerializer · class · L181-L195 — class TokenSerializer(serializers.ModelSerializer)
- Meta · class · L184-L195 — class Meta
- TokenCreateSerializer · class · L198-L204 — class TokenCreateSerializer(serializers.ModelSerializer)
- Meta · class · L199-L204 — class Meta
- TokenUpdateSerializer · class · L207-L220 — class TokenUpdateSerializer(serializers.ModelSerializer)
- Meta · class · L215-L220 — class Meta
