# backend/tests/arabase/test_chart_widget_type.py

- create_chart · function · L18-L29 — def create_chart(data_fixture, user=None, **kwargs)
- test_create_chart_widget_creates_a_grouped_data_source · function · L33-L39 — def test_create_chart_widget_creates_a_grouped_data_source(data_fixture)
- test_create_chart_widget_defaults_to_a_bar_chart · function · L43-L48 — def test_create_chart_widget_defaults_to_a_bar_chart(data_fixture)
- test_chart_type_is_set_on_creation · function · L52-L55 — def test_chart_type_is_set_on_creation(data_fixture)
- test_chart_widget_trash_restore_follows_its_data_source · function · L59-L67 — def test_chart_widget_trash_restore_follows_its_data_source(data_fixture)
- test_chart_widget_data_source_cannot_be_deleted_on_its_own · function · L71-L75 — def test_chart_widget_data_source_cannot_be_deleted_on_its_own(data_fixture)
- test_series_config_field_ids_are_remapped_on_import · function · L79-L91 — def test_series_config_field_ids_are_remapped_on_import(): # `series_config` is keyed by `field_<id>_<aggregation type>`, so an import # that renumbers fields has to rewrite the keys or every colour override # would be orphaned.
