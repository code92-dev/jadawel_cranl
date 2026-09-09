# backend/src/jadawel/contrib/database/formula/migrations/handler.py

- _recalculate_formula_metadata_dependencies_first_order · function · L32-L95 — def _recalculate_formula_metadata_dependencies_first_order( field: "Field", field_cache: FieldCache, recalculate_cell_values: bool, force_recreate_columns: bool, already_recalculated: Set[int], )
- FormulaMigrationHandler · class · L98-L393 — class FormulaMigrationHandler
- migrate_formulas_to_latest_version · method · L100-L133 — def migrate_formulas_to_latest_version( cls, batch_size: int = DEFAULT_FORMULA_MIGRATION_BATCH_SIZE )
- migrate_formulas · method · L136-L216 — def migrate_formulas( cls, migrations: FormulaMigrations, batch_size: int = DEFAULT_FORMULA_MIGRATION_BATCH_SIZE, )
- get_locked_formula_batch_to_update · function · L152-L170 — def get_locked_formula_batch_to_update() -> typing.Optional[QuerySet]: # In-case there is another concurrent formula migration is running we # want to lock the formulas we want to update. This effectively # serializes formula migrations running concurrently, but this is desirable # as otherwise they will often cause each other to crash due to deadlocks # if actually running concurrently.
- progress_updated · function · L181-L183 — def progress_updated(percentage, state)
- _update_formulas · method · L219-L243 — def _update_formulas( cls, locked_formula_batch: QuerySet, current_version: int, migrations: FormulaMigrations, child_progress_builder: ChildProgressBuilder, )
- _get_formula_querysets · method · L246-L314 — def _get_formula_querysets( cls, locked_formula_batch: QuerySet, current_version, migrations: FormulaMigrations, )
- get_q · function · L278-L282 — def get_q(selector: FormulaMigrationSelector)
- _do_formula_migration_operations · method · L317-L393 — def _do_formula_migration_operations( cls, formulas_to_rebuild_dependencies_for: QuerySet, formulas_to_both_calc_attrs_and_refresh_cell_values_for: QuerySet, formulas_to_only_recalculate_attributes_for: QuerySet, formulas_to_force_recreate_columns_for: QuerySet, child_progress_builder: ChildProgressBuilder, )
