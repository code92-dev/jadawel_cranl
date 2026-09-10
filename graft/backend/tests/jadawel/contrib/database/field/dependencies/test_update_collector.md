# backend/tests/jadawel/contrib/database/field/dependencies/test_update_collector.py

- test_can_add_fields_with_update_statements_in_same_starting_table · function · L16-L30 — def test_can_add_fields_with_update_statements_in_same_starting_table( api_client, data_fixture, django_assert_num_queries )
- test_updates_schedule_search_updates · function · L34-L48 — def test_updates_schedule_search_updates( api_client, data_fixture, django_assert_num_queries ): # TODO: Fix
- test_updates_set_them_to_not_need_background_update_when_not_edditing_rows · function · L52-L65 — def test_updates_set_them_to_not_need_background_update_when_not_edditing_rows( api_client, data_fixture, django_assert_num_queries ): # TODO: Fix
- test_can_add_fields_in_same_starting_table_with_row_filter · function · L69-L86 — def test_can_add_fields_in_same_starting_table_with_row_filter( api_client, data_fixture, django_assert_num_queries )
- test_can_only_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m · function · L90-L158 — def test_can_only_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m( api_client, data_fixture, django_assert_num_queries )
- test_can_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m_and_back · function · L162-L246 — def test_can_trigger_update_for_rows_joined_to_a_starting_row_across_a_m2m_and_back( api_client, data_fixture, django_assert_num_queries )
- test_update_statements_at_the_same_path_node_are_grouped_into_one · function · L250-L345 — def test_update_statements_at_the_same_path_node_are_grouped_into_one( api_client, data_fixture, django_assert_num_queries )
- test_update_statements_only_update_rows_where_values_change · function · L349-L399 — def test_update_statements_only_update_rows_where_values_change(data_fixture)
- execute_update_statement · function · L362-L374 — def execute_update_statement(update_statement)
- assert_all_rows_have_value · function · L376-L378 — def assert_all_rows_have_value(value)
- test_apply_updates_returns_only_last_updated_fields_but_update_collector_track_all_changes · function · L403-L482 — def test_apply_updates_returns_only_last_updated_fields_but_update_collector_track_all_changes( api_client, data_fixture, django_assert_num_queries )
