# backend/tests/jadawel/core/service/test_service_type.py

- _dispatch_result · function · L11-L18 — def _dispatch_result(**kwargs): # DispatchResult ships in baserow_premium, which this fork deletes for licence # reasons, so the tests that build one skip rather than failing collection.
- test_service_type_get_schema_name · function · L21-L25 — def test_service_type_get_schema_name()
- test_service_type_generate_schema · function · L28-L32 — def test_service_type_generate_schema()
- test_service_type_remove_unused_field_names · function · L92-L107 — def test_service_type_remove_unused_field_names(row, field_names, updated_row)
- test_service_type_prepare_values · function · L111-L155 — def test_service_type_prepare_values(data_fixture)
- test_dispatch_passes_field_names · function · L171-L195 — def test_dispatch_passes_field_names(field_names, expected_field_names)
- test_extract_properties · function · L198-L208 — def test_extract_properties()
- test_get_sample_data · function · L211-L222 — def test_get_sample_data()
- test_dispatch_returns_sample_data_when_simulated · function · L225-L249 — def test_dispatch_returns_sample_data_when_simulated()
- test_dispatch_even_if_simulated_when_updated · function · L252-L280 — def test_dispatch_even_if_simulated_when_updated()
- test_dispatch_even_if_simulated_without_sample_data · function · L283-L309 — def test_dispatch_even_if_simulated_without_sample_data()
