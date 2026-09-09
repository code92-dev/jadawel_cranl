# backend/tests/jadawel/contrib/builder/api/data_sources/test_public_data_source_views.py

- data_source_fixture · function · L12-L53 — def data_source_fixture(data_fixture)
- data_source_element_roles_fixture · function · L57-L89 — def data_source_element_roles_fixture(data_fixture)
- test_dispatch_data_sources_list_rows_no_elements · function · L93-L129 — def test_dispatch_data_sources_list_rows_no_elements( api_client, data_fixture, data_source_fixture )
- test_dispatch_data_sources_get_row_no_elements · function · L133-L165 — def test_dispatch_data_sources_get_row_no_elements( api_client, data_fixture, data_source_fixture )
- test_dispatch_data_sources_list_rows_with_elements · function · L169-L228 — def test_dispatch_data_sources_list_rows_with_elements( api_client, data_fixture, data_source_fixture )
- test_dispatch_data_sources_get_row_with_elements · function · L242-L299 — def test_dispatch_data_sources_get_row_with_elements( api_client, data_fixture, data_source_fixture, table_row_id, db_row_id )
- test_dispatch_data_sources_get_and_list_rows_with_elements · function · L303-L410 — def test_dispatch_data_sources_get_and_list_rows_with_elements( api_client, data_fixture, data_source_fixture, )
- test_dispatch_data_sources_list_rows_with_elements_and_role · function · L425-L513 — def test_dispatch_data_sources_list_rows_with_elements_and_role( api_client, data_fixture, data_source_element_roles_fixture, user_role, element_role, expect_fields, )
- test_dispatch_data_sources_page_visibility_all_returns_elements · function · L517-L565 — def test_dispatch_data_sources_page_visibility_all_returns_elements( api_client, data_fixture, data_source_fixture )
- test_dispatch_data_sources_page_visibility_logged_in_allow_all_returns_elements · function · L576-L642 — def test_dispatch_data_sources_page_visibility_logged_in_allow_all_returns_elements( api_client, data_fixture, data_source_fixture, roles )
- test_dispatch_data_sources_page_visibility_logged_in_returns_no_elements_for_anon · function · L646-L689 — def test_dispatch_data_sources_page_visibility_logged_in_returns_no_elements_for_anon( api_client, data_fixture, data_source_fixture )
- test_dispatch_data_sources_page_visibility_logged_in_allow_all_except · function · L754-L830 — def test_dispatch_data_sources_page_visibility_logged_in_allow_all_except( api_client, data_fixture, data_source_fixture, user_role, role_type, roles, is_allowed, )
