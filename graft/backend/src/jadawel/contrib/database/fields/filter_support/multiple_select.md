# backend/src/jadawel/contrib/database/fields/filter_support/multiple_select.py

- MultipleSelectFormulaTypeFilterSupport · class · L25-L80 — class MultipleSelectFormulaTypeFilterSupport( HasValueEmptyFilterSupport, HasValueEqualFilterSupport, HasValueContainsFilterSupport, HasValueContainsWordFilterSupport, )
- get_all_empty_query · method · L31-L48 — def get_all_empty_query( self, field_name: str, model_field: Field, field: "JadawelField", in_array: bool = True, ) -> OptionallyAnnotatedQ
- get_in_array_empty_query · method · L50-L57 — def get_in_array_empty_query( self, field_name, model_field, field: "JadawelField" ) -> OptionallyAnnotatedQ: # Use get_jsonb_has_any_in_value_filter_expr with size() to check if the array # is empty.
- get_in_array_is_query · method · L59-L66 — def get_in_array_is_query( self, field_name: str, value: List[int], model_field: Field, field: "JadawelField", ) -> OptionallyAnnotatedQ
- get_in_array_contains_query · method · L68-L73 — def get_in_array_contains_query( self, field_name: str, value: str, model_field: Field, field: "JadawelField" ) -> OptionallyAnnotatedQ
- get_in_array_contains_word_query · method · L75-L80 — def get_in_array_contains_word_query( self, field_name: str, value: str, model_field: Field, field: "JadawelField" ) -> OptionallyAnnotatedQ
