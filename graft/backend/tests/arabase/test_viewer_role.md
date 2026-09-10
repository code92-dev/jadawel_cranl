# backend/tests/arabase/test_viewer_role.py

- viewer_setup · function · L21-L40 — def viewer_setup(data_fixture)
- auth · function · L43-L44 — def auth(token)
- decoration_payload · function · L47-L52 — def decoration_payload(setup)
- test_viewer_role_manager_is_registered · function · L72-L75 — def test_viewer_role_manager_is_registered()
- create_body · function · L78-L90 — def create_body(resource, setup)
- test_viewer_cannot_create_view_configuration · function · L97-L109 — def test_viewer_cannot_create_view_configuration( api_client, data_fixture, viewer_setup, resource )
- test_viewer_can_read_but_not_change_decorations · function · L113-L149 — def test_viewer_can_read_but_not_change_decorations( api_client, data_fixture, viewer_setup )
- test_member_still_manages_view_configuration · function · L153-L170 — def test_member_still_manages_view_configuration( api_client, data_fixture, viewer_setup )
- test_admin_can_assign_the_viewer_role · function · L174-L203 — def test_admin_can_assign_the_viewer_role(api_client, data_fixture, viewer_setup)
- test_viewer_denied_operations_surface_in_permissions_object · function · L207-L219 — def test_viewer_denied_operations_surface_in_permissions_object(viewer_setup)
