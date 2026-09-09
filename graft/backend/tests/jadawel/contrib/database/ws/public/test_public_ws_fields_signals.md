# backend/tests/jadawel/contrib/database/ws/public/test_public_ws_fields_signals.py

- MatchDictSubSet · class · L10-L20 — class MatchDictSubSet(object)
- __init__ · method · L11-L12 — def __init__(self, sub_set)
- __eq__ · method · L14-L17 — def __eq__(self, other)
- __repr__ · method · L19-L20 — def __repr__(self)
- test_when_field_created_public_views_are_sent_field_created_with_restricted_related · function · L25-L81 — def test_when_field_created_public_views_are_sent_field_created_with_restricted_related( mock_broadcast_to_channel_group, data_fixture, django_assert_num_queries, public_realtime_view_tester, )
- test_when_field_deleted_public_views_are_field_deleted_with_restricted_related · function · L86-L135 — def test_when_field_deleted_public_views_are_field_deleted_with_restricted_related( mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester )
- test_when_field_restored_public_views_sent_event_with_restricted_related_fields · function · L140-L195 — def test_when_field_restored_public_views_sent_event_with_restricted_related_fields( mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester )
- test_when_field_updated_public_views_are_sent_event_with_restricted_related · function · L200-L254 — def test_when_field_updated_public_views_are_sent_event_with_restricted_related( mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester )
- test_cover_image_is_always_included_in_field_update_signal · function · L259-L295 — def test_cover_image_is_always_included_in_field_update_signal( mock_broadcast_to_channel_group, data_fixture, public_realtime_view_tester )
