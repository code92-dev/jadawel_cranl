# backend/tests/arabase/test_workspace_activity.py

- _set_created_on · function · L14-L21 — def _set_created_on(model, row, when)
- test_series_is_dense_and_ordered_oldest_first · function · L25-L51 — def test_series_is_dense_and_ordered_oldest_first(data_fixture)
- test_counts_span_tables_and_databases_but_skip_trashed_rows · function · L55-L72 — def test_counts_span_tables_and_databases_but_skip_trashed_rows(data_fixture)
- test_rows_outside_the_window_are_excluded · function · L76-L90 — def test_rows_outside_the_window_are_excluded(data_fixture)
- test_window_is_clamped_and_empty_workspace_is_not_an_error · function · L94-L107 — def test_window_is_clamped_and_empty_workspace_is_not_an_error(data_fixture)
- test_endpoint_returns_series_for_a_member · function · L111-L128 — def test_endpoint_returns_series_for_a_member(api_client, data_fixture)
- test_endpoint_clamps_a_malformed_days_parameter · function · L132-L145 — def test_endpoint_clamps_a_malformed_days_parameter(api_client, data_fixture)
- test_endpoint_refuses_a_workspace_the_user_is_not_in · function · L149-L162 — def test_endpoint_refuses_a_workspace_the_user_is_not_in(api_client, data_fixture)
- test_endpoint_404s_for_a_workspace_that_does_not_exist · function · L166-L175 — def test_endpoint_404s_for_a_workspace_that_does_not_exist(api_client, data_fixture)
