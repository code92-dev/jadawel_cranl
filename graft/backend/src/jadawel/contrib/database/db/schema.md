# backend/src/jadawel/contrib/database/db/schema.py

- PostgresqlLenientDatabaseSchemaEditor · class · L12-L210 — class PostgresqlLenientDatabaseSchemaEditor
- __init__ · method · L26-L37 — def __init__( self, *args, alter_column_prepare_old_value="", alter_column_prepare_new_value="", force_alter_column=False, **kwargs, )
- _alter_field · method · L39-L91 — def _alter_field( self, model, old_field, new_field, old_type, new_type, old_db_params, new_db_params, strict=False, )
- _alter_column_type_sql · method · L93-L205 — def _alter_column_type_sql( self, model, old_field, new_field, new_type, old_collation, new_collation ): # Cast when data type changed. # Make ALTER TYPE with SERIAL make sense.
- _field_should_be_altered · method · L207-L210 — def _field_should_be_altered(self, old_field, new_field)
- lenient_schema_editor · function · L214-L253 — def lenient_schema_editor( alter_column_prepare_old_value=None, alter_column_prepare_new_value=None, force_alter_column=False, )
- _build_schema_editor_class · function · L256-L264 — def _build_schema_editor_class(name, classes)
- optional_atomic · function · L268-L273 — def optional_atomic(atomic=True)
- SafeJadawelPostgresSchemaEditor · class · L276-L391 — class SafeJadawelPostgresSchemaEditor
- create_model · method · L282-L294 — def create_model(self, model)
- create_model_tracking_created_m2ms · method · L296-L316 — def create_model_tracking_created_m2ms( self, model, already_created_through_table_names: Optional[Set[str]] = None )
- delete_model · method · L318-L356 — def delete_model(self, model)
- ensure_single_column_index · method · L358-L369 — def ensure_single_column_index(self, model, field)
- ensure_m2m_field_indexes · method · L371-L382 — def ensure_m2m_field_indexes(self, field)
- add_field · method · L384-L391 — def add_field(self, model, field)
- safe_django_schema_editor · function · L395-L437 — def safe_django_schema_editor(atomic=True, name=None, classes=None, **kwargs)
