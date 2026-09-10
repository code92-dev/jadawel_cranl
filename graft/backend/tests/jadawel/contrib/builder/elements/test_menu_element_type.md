# backend/tests/jadawel/contrib/builder/elements/test_menu_element_type.py

- menu_element_fixture · function · L20-L34 — def menu_element_fixture(data_fixture)
- test_create_menu_element · function · L38-L42 — def test_create_menu_element(menu_element_fixture)
- test_update_menu_element · function · L53-L63 — def test_update_menu_element(menu_element_fixture, orientation)
- test_add_menu_item · function · L97-L123 — def test_add_menu_item(menu_element_fixture, name, item_type, variant)
- test_add_sub_link · function · L127-L176 — def test_add_sub_link(menu_element_fixture)
- test_update_menu_item · function · L224-L271 — def test_update_menu_item(menu_element_fixture, field, value)
- test_workflow_action_removed_when_menu_item_deleted · function · L275-L305 — def test_workflow_action_removed_when_menu_item_deleted( menu_element_fixture, data_fixture )
- test_specific_workflow_action_removed_when_menu_item_deleted · function · L309-L355 — def test_specific_workflow_action_removed_when_menu_item_deleted( menu_element_fixture, data_fixture )
- test_all_workflow_actions_removed_when_menu_element_deleted · function · L359-L400 — def test_all_workflow_actions_removed_when_menu_element_deleted( menu_element_fixture, data_fixture )
- test_import_export · function · L404-L479 — def test_import_export(menu_element_fixture, data_fixture)
- test_delete_duplicated_menu_doesnt_affect_initial_element · function · L483-L521 — def test_delete_duplicated_menu_doesnt_affect_initial_element( menu_element_fixture, data_fixture )
