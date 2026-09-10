# backend/tests/jadawel/contrib/builder/elements/test_element_permission_manager.py

- test_element_visibility_permission_manager_check_permission · function · L21-L136 — def test_element_visibility_permission_manager_check_permission(data_fixture)
- test_element_visibility_permission_manager_filter_queryset · function · L140-L255 — def test_element_visibility_permission_manager_filter_queryset( data_fixture, stub_user_source_registry, )
- ab_builder_user_page · function · L259-L272 — def ab_builder_user_page(data_fixture)
- test_permission_check_fails_if_logged_in_and_role_not_allowed · function · L376-L458 — def test_permission_check_fails_if_logged_in_and_role_not_allowed( ab_builder_user_page, data_fixture, role, roles, role_type, expected_check_result, )
- test_queryset_only_includes_elements_allowed_by_role · function · L558-L612 — def test_queryset_only_includes_elements_allowed_by_role( ab_builder_user_page, data_fixture, role, roles, role_type, element_count, )
- test_queryset_excludes_all_child_elements · function · L667-L747 — def test_queryset_excludes_all_child_elements( ab_builder_user_page, data_fixture, user_role, parent_element_roles, chid_element_roles, parent_visibility_type, child_visibility_type, role_type, logged_in, )
- test_auth_user_can_view_element_returns_expected_bool · function · L843-L880 — def test_auth_user_can_view_element_returns_expected_bool( ab_builder_user_page, data_fixture, role, roles, role_type, expected_bool_result, )
- test_get_roles_returns_role · function · L893-L914 — def test_get_roles_returns_role( ab_builder_user_page, role, expected_role, )
- test_auth_user_can_view_element_returns_true · function · L938-L973 — def test_auth_user_can_view_element_returns_true( ab_builder_user_page, data_fixture, role, roles, role_type, )
- test_page_visibility_applied_to_workflow_actions_queryset · function · L1070-L1137 — def test_page_visibility_applied_to_workflow_actions_queryset( ab_builder_user_page, data_fixture, page_visibility, page_role_type, page_roles, element_visibility, element_role_type, element_roles, user_role, expected_count, )
