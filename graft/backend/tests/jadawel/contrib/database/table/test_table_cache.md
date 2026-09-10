# backend/tests/jadawel/contrib/database/table/test_table_cache.py

- test_creating_link_row_field_invalidates_its_link_row_related_cache · function · L11-L34 — def test_creating_link_row_field_invalidates_its_link_row_related_cache( data_fixture, django_assert_num_queries )
- test_converting_link_row_field_to_another_type_invalidates_its_related_tables_cache · function · L38-L55 — def test_converting_link_row_field_to_another_type_invalidates_its_related_tables_cache( data_fixture, )
- test_converting_link_row_field_to_point_at_another_table_invalidates_its_related_tables_cache · function · L59-L83 — def test_converting_link_row_field_to_point_at_another_table_invalidates_its_related_tables_cache( data_fixture, )
- test_converting_text_to_link_row_field_invalidates_its_related_tables_cache · function · L87-L111 — def test_converting_text_to_link_row_field_invalidates_its_related_tables_cache( data_fixture, )
- test_can_disable_model_cache · function · L116-L148 — def test_can_disable_model_cache( data_fixture, )
- test_trashing_link_row_field_invalidates_its_related_tables_cache · function · L152-L169 — def test_trashing_link_row_field_invalidates_its_related_tables_cache( data_fixture, )
- test_restoring_link_row_field_invalidates_its_related_tables_cache · function · L173-L192 — def test_restoring_link_row_field_invalidates_its_related_tables_cache( data_fixture, )
- test_deleting_field_invalidates_tables_model_cache · function · L196-L206 — def test_deleting_field_invalidates_tables_model_cache(data_fixture)
