# backend/tests/jadawel/performance/test_formula_performance.py

- test_adding_a_formula_field_compared_to_normal_field_isnt_slow · function · L23-L46 — def test_adding_a_formula_field_compared_to_normal_field_isnt_slow(data_fixture)
- test_very_nested_formula_field_change · function · L54-L87 — def test_very_nested_formula_field_change(data_fixture, django_assert_num_queries)
- test_creating_very_nested_formula_field · function · L95-L114 — def test_creating_very_nested_formula_field(data_fixture)
- test_altering_very_nested_formula_field · function · L122-L150 — def test_altering_very_nested_formula_field(data_fixture, django_assert_num_queries)
- test_getting_data_from_a_very_nested_formula_field · function · L158-L183 — def test_getting_data_from_a_very_nested_formula_field(data_fixture, api_client)
- test_getting_data_from_normal_table · function · L191-L215 — def test_getting_data_from_normal_table(data_fixture, api_client)
- add_fan_out_of · function · L218-L291 — def add_fan_out_of( api_client, data_fixture, user, token, table, fanout, depth, profiler=None, )
- test_fanout_one_off · function · L296-L316 — def test_fanout_one_off(data_fixture, api_client, django_assert_num_queries)
- test_fanout · function · L321-L368 — def test_fanout(data_fixture, api_client, django_assert_num_queries)
