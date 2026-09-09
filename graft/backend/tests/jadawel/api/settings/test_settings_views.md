# backend/tests/jadawel/api/settings/test_settings_views.py

- test_get_settings · function · L19-L43 — def test_get_settings(api_client)
- test_require_first_admin_user_is_false_after_admin_creation · function · L47-L76 — def test_require_first_admin_user_is_false_after_admin_creation( api_client, data_fixture )
- test_get_instance_id · function · L80-L112 — def test_get_instance_id(api_client, data_fixture)
- test_update_settings · function · L116-L171 — def test_update_settings(api_client, data_fixture)
- test_update_co_branding_logo · function · L175-L201 — def test_update_co_branding_logo(api_client, data_fixture)
- test_update_show_jadawel_help_request · function · L205-L226 — def test_update_show_jadawel_help_request(api_client, data_fixture)
- test_register_settings_data_type · function · L230-L246 — def test_register_settings_data_type(api_client, data_fixture)
- TmpSettingsDataType · class · L233-L237 — class TmpSettingsDataType(SettingsDataType)
- get_settings_data · method · L236-L237 — def get_settings_data(self, request) -> dict
- test_update_email_verification_settings_invalid · function · L251-L263 — def test_update_email_verification_settings_invalid(api_client, data_fixture, value)
- test_update_email_verification_settings · function · L267-L277 — def test_update_email_verification_settings(api_client, data_fixture)
- test_partial_update_does_not_overwrite_email_verification · function · L281-L306 — def test_partial_update_does_not_overwrite_email_verification(api_client, data_fixture)
