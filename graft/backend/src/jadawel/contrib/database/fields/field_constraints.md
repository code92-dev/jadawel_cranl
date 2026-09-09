# backend/src/jadawel/contrib/database/fields/field_constraints.py

- FieldValueConstraint · class · L21-L42 — class FieldValueConstraint(Instance)
- get_constraint_name · method · L30-L31 — def get_constraint_name(self, field, field_name)
- build_field_constraint · method · L33-L36 — def build_field_constraint(self, field, field_name, **kwargs)
- get_compatible_field_types · method · L38-L39 — def get_compatible_field_types(self) -> List[str]
- is_field_type_compatible · method · L41-L42 — def is_field_type_compatible(self, field_type: FieldType)
- UniqueWithEmptyConstraint · class · L45-L66 — class UniqueWithEmptyConstraint(FieldValueConstraint)
- build_field_constraint · method · L50-L58 — def build_field_constraint(self, field, field_name, **kwargs)
- get_compatible_field_types · method · L60-L66 — def get_compatible_field_types(self) -> List[str]
- TextTypeUniqueWithEmptyConstraint · class · L69-L91 — class TextTypeUniqueWithEmptyConstraint(FieldValueConstraint)
- build_field_constraint · method · L74-L83 — def build_field_constraint(self, field, field_name, **kwargs)
- get_compatible_field_types · method · L85-L91 — def get_compatible_field_types(self) -> List[str]
- RatingTypeUniqueWithEmptyConstraint · class · L94-L111 — class RatingTypeUniqueWithEmptyConstraint(FieldValueConstraint)
- build_field_constraint · method · L99-L108 — def build_field_constraint(self, field, field_name, **kwargs)
- get_compatible_field_types · method · L110-L111 — def get_compatible_field_types(self) -> List[str]
