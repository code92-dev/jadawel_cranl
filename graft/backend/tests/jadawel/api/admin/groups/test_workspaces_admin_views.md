# backend/tests/jadawel/api/admin/groups/test_workspaces_admin_views.py

- test_list_admin_workspaces · function · L19-L185 — def test_list_admin_workspaces(api_client, data_fixture, django_assert_num_queries)
- test_delete_workspace · function · L190-L207 — def test_delete_workspace(api_client, data_fixture)
- test_cant_delete_template_workspace · function · L212-L221 — def test_cant_delete_template_workspace(api_client, data_fixture)
- test_non_admin_list_workspaces_as_options · function · L226-L238 — def test_non_admin_list_workspaces_as_options(api_client, data_fixture)
- test_admin_list_workspaces_as_options · function · L243-L280 — def test_admin_list_workspaces_as_options(api_client, data_fixture)
- test_admin_list_workspaces_as_options_filter_by_ids · function · L285-L324 — def test_admin_list_workspaces_as_options_filter_by_ids(api_client, data_fixture)
- test_admin_list_workspaces_as_options_filter_by_invalid_ids · function · L329-L377 — def test_admin_list_workspaces_as_options_filter_by_invalid_ids( api_client, data_fixture )
