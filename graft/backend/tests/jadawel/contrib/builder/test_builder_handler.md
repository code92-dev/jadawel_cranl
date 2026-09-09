# backend/tests/jadawel/contrib/builder/test_builder_handler.py

- fake_user_source_user · function · L19-L24 — def fake_user_source_user(role: str = "") -> UserSourceUser
- test_get_builder · function · L28-L30 — def test_get_builder(data_fixture)
- test_get_builder_does_not_exist · function · L34-L36 — def test_get_builder_does_not_exist(data_fixture)
- test_get_builder_select_related_theme_config · function · L40-L53 — def test_get_builder_select_related_theme_config( data_fixture, django_assert_num_queries )
- test_get_builder_used_properties_cache_key_returned_expected_cache_key · function · L81-L87 — def test_get_builder_used_properties_cache_key_returned_expected_cache_key( user, expected_cache_key )
- test_public_allowed_properties_is_cached · function · L91-L154 — def test_public_allowed_properties_is_cached(data_fixture, django_assert_num_queries)
- test_aggregate_user_source_counts · function · L158-L190 — def test_aggregate_user_source_counts(data_fixture)
- test_builder_get_published_applications · function · L194-L221 — def test_builder_get_published_applications(data_fixture)
