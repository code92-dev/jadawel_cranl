# backend/src/jadawel/contrib/database/formula/types/filter_support.py

- JadawelFormulaArrayFilterSupportMixin · class · L23-L100 — class JadawelFormulaArrayFilterSupportMixin( HasAllValuesEqualFilterSupport, HasValueEmptyFilterSupport, HasValueEqualFilterSupport, HasValueContainsFilterSupport, HasValueContainsWordFilterSupport, HasValueLengthIsLowerThanFilterSupport, HasNumericValueComparableToFilterSupport, )
- empty_query · method · L36-L43 — def empty_query(self, field_name, model_field, field)
- get_in_array_empty_value · method · L45-L47 — def get_in_array_empty_value(self, field)
- get_in_array_empty_query · method · L49-L53 — def get_in_array_empty_query(self, field_name, model_field, field)
- get_in_array_is_query · method · L55-L59 — def get_in_array_is_query(self, field_name, value, model_field, field)
- get_in_array_contains_query · method · L61-L65 — def get_in_array_contains_query(self, field_name, value, model_field, field)
- get_in_array_contains_word_query · method · L67-L71 — def get_in_array_contains_word_query(self, field_name, value, model_field, field)
- get_in_array_length_is_lower_than_query · method · L73-L79 — def get_in_array_length_is_lower_than_query( self, field_name, value, model_field, field )
- get_has_all_values_equal_query · method · L81-L87 — def get_has_all_values_equal_query( self, field_name: str, value: str, model_field: models.Field, field: "Field" ) -> "OptionallyAnnotatedQ"
- get_has_numeric_value_comparable_to_filter_query · method · L89-L100 — def get_has_numeric_value_comparable_to_filter_query( self, field_name: str, value: str, model_field: models.Field, field: "Field", comparison_op: ComparisonOperator, ) -> "OptionallyAnnotatedQ"
