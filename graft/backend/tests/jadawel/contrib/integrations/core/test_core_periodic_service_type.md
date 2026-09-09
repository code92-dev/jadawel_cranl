# backend/tests/jadawel/contrib/integrations/core/test_core_periodic_service_type.py

- test_periodic_trigger_service_type_generate_schema · function · L33-L54 — def test_periodic_trigger_service_type_generate_schema(data_fixture)
- test_periodic_trigger_node_creation_and_property_updates · function · L58-L112 — def test_periodic_trigger_node_creation_and_property_updates(data_fixture)
- test_periodic_service_prepare_values_validates_minute_minimum · function · L120-L144 — def test_periodic_service_prepare_values_validates_minute_minimum(data_fixture)
- test_call_periodic_services_in_draft_workflow · function · L151-L172 — def test_call_periodic_services_in_draft_workflow(mock_start_workflow, data_fixture)
- test_call_periodic_services_in_paused_workflow · function · L179-L200 — def test_call_periodic_services_in_paused_workflow(mock_start_workflow, data_fixture)
- test_call_periodic_services_that_are_locked · function · L207-L233 — def test_call_periodic_services_that_are_locked(mock_start_workflow, data_fixture)
- test_call_multiple_periodic_services_that_are_due · function · L240-L296 — def test_call_multiple_periodic_services_that_are_due( mock_async_start_workflow, data_fixture )
- test_call_periodic_services_that_are_due · function · L304-L359 — def test_call_periodic_services_that_are_due( data_fixture, service_kwargs, frozen_time, should_be_called )
- check_service_count · function · L327-L343 — def check_service_count(services, event_payload)
