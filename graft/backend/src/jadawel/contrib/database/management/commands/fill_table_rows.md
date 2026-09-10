# backend/src/jadawel/contrib/database/management/commands/fill_table_rows.py

- underscore · function · L26-L31 — def underscore(word: str) -> str
- Command · class · L34-L181 — class Command(BaseCommand)
- add_arguments · method · L37-L74 — def add_arguments(self, parser)
- handle · method · L76-L181 — def handle(self, *args, **options)
- extract_table_fields · function · L184-L202 — def extract_table_fields(model) -> List[Tuple[str, str]]
- validate_replicated_tables · function · L205-L233 — def validate_replicated_tables(source_table_model, replicated_table_models)
- generate_values_for_one_or_more_tables · function · L236-L267 — def generate_values_for_one_or_more_tables(models, fake, cache)
- create_row_instance_and_relations · function · L270-L288 — def create_row_instance_and_relations(values, table, model, fake, cache, order): # Based on the random_value function we have for each type we can # build a dict with a random value for each field.
- create_many_to_many_relations · function · L291-L326 — def create_many_to_many_relations(model, rows): # Construct an object where the key is the field name of the many to many # field that must be populated. The value contains the objects that must be # inserted in bulk.
- bulk_create_rows · function · L329-L334 — def bulk_create_rows(model, rows)
- fill_table_rows · function · L337-L404 — def fill_table_rows( limit, table, batch_size=-1, source_table_model=None, replicated_table_models=None, skip_tsvectors=False, )
- progress_updated · function · L366-L369 — def progress_updated(percentage, state=None)
