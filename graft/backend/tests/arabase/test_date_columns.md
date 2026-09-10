# backend/tests/arabase/test_date_columns.py

- TestIsDatetimeColumn · class · L34-L69 — class TestIsDatetimeColumn
- test_a_plain_date_field_is_not_a_datetime · method · L35-L39 — def test_a_plain_date_field_is_not_a_datetime(self, data_fixture)
- test_a_date_field_with_time_is_a_datetime · method · L41-L45 — def test_a_date_field_with_time_is_a_datetime(self, data_fixture)
- test_created_on_is_a_datetime_even_with_the_time_hidden · method · L47-L61 — def test_created_on_is_a_datetime_even_with_the_time_hidden(self, data_fixture)
- test_an_unknown_column_falls_back_to_the_flag · method · L63-L69 — def test_an_unknown_column_falls_back_to_the_flag(self, data_fixture)
- TestFieldTzinfo · class · L73-L96 — class TestFieldTzinfo
- test_no_forced_timezone_leaves_the_default_alone · method · L74-L78 — def test_no_forced_timezone_leaves_the_default_alone(self, data_fixture)
- test_a_forced_timezone_is_honoured · method · L80-L89 — def test_a_forced_timezone_is_honoured(self, data_fixture)
- test_an_unusable_timezone_does_not_raise · method · L91-L96 — def test_an_unusable_timezone_does_not_raise(self, data_fixture)
- agenda · function · L100-L156 — def agenda(data_fixture)
- _configure · function · L159-L167 — def _configure(setup, **kwargs)
- _names · function · L170-L176 — def _names(setup)
- test_the_last_day_of_the_window_is_included · function · L180-L189 — def test_the_last_day_of_the_window_is_included(agenda)
- test_overdue_rows_are_bounded_on_the_past_side · function · L193-L205 — def test_overdue_rows_are_bounded_on_the_past_side(agenda)
