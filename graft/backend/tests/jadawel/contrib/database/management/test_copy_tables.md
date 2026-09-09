# backend/tests/jadawel/contrib/database/management/test_copy_tables.py

- Struct · class · L4-L11 — class Struct
- __init__ · method · L10-L11 — def __init__(self, **entries)
- fake_connection · function · L14-L33 — def fake_connection(name, tables)
- table_names · function · L15-L16 — def table_names()
- backup_cmd_with_tables · function · L36-L40 — def backup_cmd_with_tables(tables)
- test_a_table_already_in_the_target_db_is_not_in_the_command · function · L43-L59 — def test_a_table_already_in_the_target_db_is_not_in_the_command()
- run_command · function · L46-L47 — def run_command(command, _)
- test_a_batch_size_the_same_as_the_number_of_tables_runs_one_batch · function · L62-L81 — def test_a_batch_size_the_same_as_the_number_of_tables_runs_one_batch()
- run_command · function · L65-L66 — def run_command(command, env)
- test_a_batch_size_one_more_than_the_number_of_tables_runs_two_batches · function · L84-L104 — def test_a_batch_size_one_more_than_the_number_of_tables_runs_two_batches()
- run_command · function · L87-L88 — def run_command(command, env)
- test_the_final_batch_includes_all_remaining_tables · function · L107-L128 — def test_the_final_batch_includes_all_remaining_tables()
- run_command · function · L110-L111 — def run_command(command, env)
- test_a_batch_with_some_tables_ignored_wont_merge_with_the_next_batch · function · L131-L151 — def test_a_batch_with_some_tables_ignored_wont_merge_with_the_next_batch()
- run_command · function · L134-L135 — def run_command(command, env)
