# backend/src/jadawel/contrib/database/fields/filter_support/formula.py

- FormulaFieldTypeArrayFilterSupport · class · L24-L136 — class FormulaFieldTypeArrayFilterSupport( HasAllValuesEqualFilterSupport, HasValueEqualFilterSupport, HasValueEmptyFilterSupport, HasValueContainsFilterSupport, HasValueContainsWordFilterSupport, HasValueLengthIsLowerThanFilterSupport, HasNumericValueComparableToFilterSupport, )
- get_in_array_is_query · method · L39-L53 — def get_in_array_is_query( self, field_name: str, value: str, model_field: models.Field, field: "FormulaField", ) -> OptionallyAnnotatedQ
- get_in_array_empty_value · method · L55-L61 — def get_in_array_empty_value(self, field: "Field") -> any
- get_in_array_empty_query · method · L63-L71 — def get_in_array_empty_query(self, field_name, model_field, field: "FormulaField")
- get_in_array_contains_query · method · L73-L83 — def get_in_array_contains_query( self, field_name, value, model_field, field: "FormulaField" )
- get_in_array_contains_word_query · method · L85-L95 — def get_in_array_contains_word_query( self, field_name, value, model_field, field: "FormulaField" )
- get_in_array_length_is_lower_than_query · method · L97-L107 — def get_in_array_length_is_lower_than_query( self, field_name, value, model_field, field: "FormulaField" )
- get_has_all_values_equal_query · method · L109-L119 — def get_has_all_values_equal_query( self, field_name, value, model_field, field: "FormulaField" )
- get_has_numeric_value_comparable_to_filter_query · method · L121-L136 — def get_has_numeric_value_comparable_to_filter_query( self, field_name: str, value: str, model_field: models.Field, field: "Field", comparison_op: ComparisonOperator, ) -> OptionallyAnnotatedQ
