# backend/tests/jadawel/core/app_auth_providers/test_app_auth_handler.py

- pytest_generate_tests · function · L13-L21 — def pytest_generate_tests(metafunc)
- test_create_app_auth_provider · function · L25-L42 — def test_create_app_auth_provider( data_fixture, app_auth_provider_type: AppAuthProviderType )
- test_get_app_auth_provider · function · L46-L51 — def test_get_app_auth_provider(data_fixture)
- test_get_app_auth_provider_does_not_exist · function · L55-L58 — def test_get_app_auth_provider_does_not_exist(data_fixture)
- test_get_app_auth_providers · function · L62-L87 — def test_get_app_auth_providers(data_fixture)
- test_delete_app_auth_provider · function · L91-L97 — def test_delete_app_auth_provider(data_fixture)
- test_update_app_auth_provider · function · L101-L109 — def test_update_app_auth_provider(data_fixture)
- test_update_app_auth_provider_invalid_values · function · L113-L121 — def test_update_app_auth_provider_invalid_values(data_fixture)
- test_export_app_auth_provider · function · L125-L141 — def test_export_app_auth_provider(data_fixture)
- test_import_app_auth_provider · function · L145-L160 — def test_import_app_auth_provider(data_fixture)
- test_import_app_auth_provider_with_migrated_user_source · function · L164-L176 — def test_import_app_auth_provider_with_migrated_user_source(data_fixture)
