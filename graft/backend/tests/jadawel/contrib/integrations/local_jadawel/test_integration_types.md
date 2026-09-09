# backend/tests/jadawel/contrib/integrations/local_jadawel/test_integration_types.py

- test_create_local_jadawel_integration_with_user · function · L17-L27 — def test_create_local_jadawel_integration_with_user(data_fixture)
- test_get_local_jadawel_databases_no_databases · function · L31-L37 — def test_get_local_jadawel_databases_no_databases(data_fixture)
- test_get_local_jadawel_databases · function · L41-L77 — def test_get_local_jadawel_databases(data_fixture)
- test_get_local_jadawel_databases_number_of_queries · function · L81-L105 — def test_get_local_jadawel_databases_number_of_queries( data_fixture, django_assert_num_queries, bypass_check_permissions )
- test_get_local_jadawel_databases_performance · function · L116-L155 — def test_get_local_jadawel_databases_performance(data_fixture, api_client, profiler)
- test_get_integrations_serializer · function · L159-L252 — def test_get_integrations_serializer( api_client, data_fixture, bypass_check_permissions )
- test_after_import · function · L256-L277 — def test_after_import(data_fixture)
