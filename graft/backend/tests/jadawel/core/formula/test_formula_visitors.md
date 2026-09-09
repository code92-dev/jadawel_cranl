# backend/tests/jadawel/core/formula/test_formula_visitors.py

- MockDataProvider · class · L21-L28 — class MockDataProvider(DataProviderType)
- is_valid · method · L24-L25 — def is_valid(self, path: List[str])
- get_data_chunk · method · L27-L28 — def get_data_chunk(self, dispatch_context: DispatchContext, path: List[str])
- mock_registry · function · L32-L35 — def mock_registry()
- parse_and_visit_formula · function · L38-L43 — def parse_and_visit_formula(formula: str, registry=None)
- test_get_with_no_arguments_raises_invalid_number_of_args · function · L46-L51 — def test_get_with_no_arguments_raises_invalid_number_of_args(mock_registry)
- test_get_with_two_arguments_raises_invalid_number_of_args · function · L54-L61 — def test_get_with_two_arguments_raises_invalid_number_of_args(mock_registry)
- test_get_with_empty_provider_name_raises_syntax_error · function · L64-L71 — def test_get_with_empty_provider_name_raises_syntax_error( mock_registry, )
- test_get_with_nonexistent_provider_raises_instance_type_does_not_exist · function · L74-L81 — def test_get_with_nonexistent_provider_raises_instance_type_does_not_exist( mock_registry, )
- test_get_with_valid_provider_calls_is_valid · function · L84-L88 — def test_get_with_valid_provider_calls_is_valid(mock_registry)
- test_get_as_child_formula_is_valid · function · L91-L100 — def test_get_as_child_formula_is_valid(mock_registry)
