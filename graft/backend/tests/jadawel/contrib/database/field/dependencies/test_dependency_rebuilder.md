# backend/tests/jadawel/contrib/database/field/dependencies/test_dependency_rebuilder.py

- _unwrap_ids · function · L17-L18 — def _unwrap_ids(qs)
- test_formula_fields_will_be_rebuilt_to_depend_on_each_other · function · L22-L45 — def test_formula_fields_will_be_rebuilt_to_depend_on_each_other( api_client, data_fixture, django_assert_num_queries )
- _assert_rebuilding_changes_nothing · function · L48-L60 — def _assert_rebuilding_changes_nothing(cache, field_to_rebuild)
- test_rebuilding_with_a_circular_ref_will_raise · function · L64-L94 — def test_rebuilding_with_a_circular_ref_will_raise( api_client, data_fixture, django_assert_num_queries )
- test_rebuilding_a_link_row_field_creates_dependencies_with_vias · function · L98-L122 — def test_rebuilding_a_link_row_field_creates_dependencies_with_vias( api_client, data_fixture, django_assert_num_queries )
- test_trashing_a_link_row_field_breaks_vias · function · L126-L166 — def test_trashing_a_link_row_field_breaks_vias( api_client, data_fixture, django_assert_num_queries )
- test_trashing_a_lookup_target_still_has_the_dep_depend_on_the_through_field · function · L170-L215 — def test_trashing_a_lookup_target_still_has_the_dep_depend_on_the_through_field( data_fixture, )
- test_str_of_field_dependency_uniquely_identifies_it · function · L219-L324 — def test_str_of_field_dependency_uniquely_identifies_it( api_client, data_fixture, django_assert_num_queries )
- test_trashing_and_restoring_a_field_recreate_dependencies_correctly · function · L328-L373 — def test_trashing_and_restoring_a_field_recreate_dependencies_correctly(data_fixture)
- test_even_with_circular_dependencies_queries_finish_in_time · function · L377-L397 — def test_even_with_circular_dependencies_queries_finish_in_time(data_fixture): # This should never happen, but if somehow circular dependencies are created # we should still be able to get the dependencies of a field without running # into an infinite loop in the recursive query.
