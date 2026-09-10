# backend/tests/jadawel/contrib/database/search/test_workspace_search_handler.py

- test_handler_basic_search_workflow · function · L13-L31 — def test_handler_basic_search_workflow(data_fixture)
- test_search_handler_query_count · function · L36-L53 — def test_search_handler_query_count(data_fixture, django_assert_max_num_queries)
- do_search · function · L43-L46 — def do_search(q: str)
- test_search_handler_with_pagination · function · L58-L88 — def test_search_handler_with_pagination(data_fixture)
- test_search_handler_permission_filtering · function · L93-L122 — def test_search_handler_permission_filtering(data_fixture)
- test_search_handler_priority_ordering · function · L127-L147 — def test_search_handler_priority_ordering(data_fixture)
- test_search_context_creation · function · L152-L169 — def test_search_context_creation(data_fixture)
- test_search_handler_has_more_logic · function · L174-L200 — def test_search_handler_has_more_logic(data_fixture)
- test_search_handler_result_serialization · function · L205-L223 — def test_search_handler_result_serialization(data_fixture)
- test_search_handler_with_special_characters · function · L228-L267 — def test_search_handler_with_special_characters(data_fixture)
- test_workspace_row_search_handler_with_interesting_database · function · L272-L369 — def test_workspace_row_search_handler_with_interesting_database(data_fixture)
- do_search · function · L295-L298 — def do_search(q: str)
- _row_results · function · L300-L301 — def _row_results(r)
- _assert_row_shape · function · L303-L315 — def _assert_row_shape(item): # Title should now contain the primary field value, not "Row #"
