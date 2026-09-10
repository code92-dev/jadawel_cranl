# backend/src/jadawel/contrib/database/fields/filter_support/single_select.py

- SingleSelectFormulaTypeFilterSupport · class · L23-L55 — class SingleSelectFormulaTypeFilterSupport( HasValueEmptyFilterSupport, HasValueEqualFilterSupport, HasValueContainsFilterSupport, HasValueContainsWordFilterSupport, )
- get_in_array_empty_value · method · L29-L30 — def get_in_array_empty_value(self, field: "Field") -> any
- get_in_array_is_query · method · L32-L41 — def get_in_array_is_query( self, field_name: str, value: List[int], model_field: models.Field, field: "Field", ) -> OptionallyAnnotatedQ
- get_in_array_contains_query · method · L43-L48 — def get_in_array_contains_query( self, field_name: str, value: str, model_field: models.Field, field: "Field" ) -> OptionallyAnnotatedQ
- get_in_array_contains_word_query · method · L50-L55 — def get_in_array_contains_word_query( self, field_name: str, value: str, model_field: models.Field, field: "Field" ) -> OptionallyAnnotatedQ
