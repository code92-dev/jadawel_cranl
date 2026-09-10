# backend/tests/jadawel/api/health/test_email_tester_views.py

- test_anonymous_user_cant_trigger_test_email · function · L10-L15 — def test_anonymous_user_cant_trigger_test_email(data_fixture, api_client)
- test_non_staff_user_cant_trigger_test_email · function · L19-L27 — def test_non_staff_user_cant_trigger_test_email(data_fixture, api_client)
- test_staff_user_can_trigger_test_email · function · L32-L48 — def test_staff_user_can_trigger_test_email( patched_get_connection, data_fixture, api_client )
- test_staff_user_can_trigger_test_email_and_see_error_if_fails · function · L53-L69 — def test_staff_user_can_trigger_test_email_and_see_error_if_fails( patched_get_connection, data_fixture, api_client )
