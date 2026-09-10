# backend/src/jadawel/api/polymorphic.py

- BasePolymorphicSerializer · class · L7-L211 — class BasePolymorphicSerializer(serializers.Serializer)
- get_type_from_type_name · method · L83-L84 — def get_type_from_type_name(self, name)
- get_type_from_instance · method · L86-L87 — def get_type_from_instance(self, instance)
- get_type_from_mapping · method · L89-L93 — def get_type_from_mapping(self, mapping)
- to_representation · method · L95-L116 — def to_representation(self, instance)
- to_internal_value · method · L118-L132 — def to_internal_value(self, data)
- create · method · L134-L145 — def create(self, validated_data)
- update · method · L147-L162 — def update(self, instance, validated_data)
- is_valid · method · L164-L188 — def is_valid(self, *args, **kwargs)
- run_validation · method · L190-L211 — def run_validation(self, data=empty)
- PolymorphicSerializer · class · L214-L217 — class PolymorphicSerializer(BasePolymorphicSerializer)
- PolymorphicRequestSerializer · class · L220-L225 — class PolymorphicRequestSerializer(BasePolymorphicSerializer)
