# backend/tests/jadawel/performance/test_field_performance.py

- test_speed_of_table_copy · function · L19-L30 — def test_speed_of_table_copy(data_fixture): # 2.2 seconds on AMD Ryzen 5900X, 32gb ram.
- test_speed_of_table_copy_via_export · function · L38-L49 — def test_speed_of_table_copy_via_export(data_fixture): # 8.84 seconds on AMD Ryzen 5900X, 32gb ram.
- test_updating_many_fields_doesnt_slow_down_get_rows · function · L57-L89 — def test_updating_many_fields_doesnt_slow_down_get_rows(data_fixture, api_client)
- profile_get · function · L92-L107 — def profile_get(api_client, grid_view, token)
