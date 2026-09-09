# backend/tests/jadawel/contrib/database/field/test_number_lookup_field_filters.py

- number_lookup_filter_proc · function · L16-L115 — def number_lookup_filter_proc( data_fixture: "Fixtures", filter_type_name: str, test_value: str, expected_rows: set[str], number_decimal_places: int = 5, )
- get_linked_rows · function · L71-L72 — def get_linked_rows(*indexes) -> list[int]
- test_number_lookup_field_has_empty_value_filter · function · L157-L160 — def test_number_lookup_field_has_empty_value_filter( data_fixture, filter_type_name, expected_rows )
- test_number_lookup_field_has_value_equal_filter · function · L198-L203 — def test_number_lookup_field_has_value_equal_filter( data_fixture, filter_type_name, test_value, expected_rows )
- test_number_lookup_field_has_value_contains_filter · function · L254-L259 — def test_number_lookup_field_has_value_contains_filter( data_fixture, filter_type_name, test_value, expected_rows )
- test_number_lookup_field_has_value_higher_than_filter · function · L315-L320 — def test_number_lookup_field_has_value_higher_than_filter( data_fixture, filter_type_name, test_value, expected_rows )
- test_number_lookup_field_has_value_higher_equal_than_filter · function · L391-L396 — def test_number_lookup_field_has_value_higher_equal_than_filter( data_fixture, filter_type_name, test_value, expected_rows )
- test_number_lookup_field_has_value_lower_equal_than_filter · function · L473-L478 — def test_number_lookup_field_has_value_lower_equal_than_filter( data_fixture, filter_type_name, test_value, expected_rows )
- test_number_lookup_field_has_value_lower_than_filter · function · L556-L561 — def test_number_lookup_field_has_value_lower_than_filter( data_fixture, filter_type_name, test_value, expected_rows )
