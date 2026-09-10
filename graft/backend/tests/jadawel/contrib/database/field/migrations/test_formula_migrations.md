# backend/tests/jadawel/contrib/database/field/migrations/test_formula_migrations.py

- assert_all_rows_are_none · function · L20-L22 — def assert_all_rows_are_none(data_fixture, field)
- assert_all_rows_are_not_none · function · L25-L29 — def assert_all_rows_are_not_none(data_fixture, field)
- assert_when_updating_formula_versions · function · L32-L56 — def assert_when_updating_formula_versions( data_fixture, given_formulas_with_version_in_the_db, when_the_migrations_are, then_formula_cell_values_are_recalculated, given_the_formula_is="1", given_the_formula_field_is=None, )
- test_assert_migrations_are_valid · function · L60-L64 — def test_assert_migrations_are_valid(): # Migrations should be ascending order starting from 1 and always incrementing only # by 1.
- test_migration_including_field_which_should_recalculate_its_attributes · function · L68-L106 — def test_migration_including_field_which_should_recalculate_its_attributes( data_fixture, )
- test_migration_excluding_field_which_shouldnt_recalculate_its_attributes · function · L110-L147 — def test_migration_excluding_field_which_shouldnt_recalculate_its_attributes( data_fixture, )
- test_migration_excluding_field_which_shouldnt_recalculate_its_attributes_from · function · L151-L188 — def test_migration_excluding_field_which_shouldnt_recalculate_its_attributes_from( data_fixture, )
- test_migration_including_field_for_dep_recalc_recalcs_its_deps · function · L192-L246 — def test_migration_including_field_for_dep_recalc_recalcs_its_deps( data_fixture, )
- test_downgrade_recalculates_attributes_and_graph_but_not_cell_values · function · L250-L290 — def test_downgrade_recalculates_attributes_and_graph_but_not_cell_values( data_fixture, )
- test_recalculate_formulas_according_to_version_needing_full_refresh · function · L294-L383 — def test_recalculate_formulas_according_to_version_needing_full_refresh( data_fixture, ): # Passing over a version that needs recalculation of cells does it
- test_recalculate_formula_that_is_broken_marks_it_as_invalid · function · L387-L434 — def test_recalculate_formula_that_is_broken_marks_it_as_invalid( data_fixture, )
- test_formula_migration_failing_when_refreshing_cell_values_marks_as_invalid · function · L441-L488 — def test_formula_migration_failing_when_refreshing_cell_values_marks_as_invalid( mock_generator_func, data_fixture, )
- test_recalculate_formulas_according_to_version · function · L492-L598 — def test_recalculate_formulas_according_to_version( data_fixture, )
- test_complex_set_of_migrations_with_different_filters · function · L602-L728 — def test_complex_set_of_migrations_with_different_filters( data_fixture, )
- test_can_force_recalculate_for_formulas_with_invalid_syntax_or_of_error_type · function · L732-L797 — def test_can_force_recalculate_for_formulas_with_invalid_syntax_or_of_error_type( data_fixture, )
