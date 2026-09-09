# backend/tests/jadawel/contrib/database/ws/test_ws_rows_signals.py

- test_row_created · function · L24-L52 — def test_row_created(mock_broadcast_to_channel_group, data_fixture)
- test_row_created_without_sending_realtime_update · function · L57-L69 — def test_row_created_without_sending_realtime_update( mock_broadcast_to_channel_group, data_fixture )
- test_row_created_with_metadata · function · L74-L93 — def test_row_created_with_metadata(mock_broadcast_to_channel_group, data_fixture)
- test_populates_with_row_id_metadata · function · L96-L108 — def test_populates_with_row_id_metadata()
- RowIdMetadata · class · L97-L106 — class RowIdMetadata(RowMetadataType)
- generate_metadata_for_rows · method · L100-L103 — def generate_metadata_for_rows( self, user, table, row_ids: List[int] ) -> Dict[int, Any]
- get_example_serializer_field · method · L105-L106 — def get_example_serializer_field(self) -> Field
- test_row_updated · function · L113-L150 — def test_row_updated(mock_broadcast_to_channel_group, data_fixture)
- test_row_updated_without_sending_realtime_update · function · L155-L172 — def test_row_updated_without_sending_realtime_update( mock_broadcast_to_channel_group, data_fixture )
- test_row_updated_with_metadata · function · L177-L202 — def test_row_updated_with_metadata(mock_broadcast_to_channel_group, data_fixture)
- test_row_deleted · function · L207-L224 — def test_row_deleted(mock_broadcast_to_channel_group, data_fixture)
- test_row_deleted_without_sending_realtime_update · function · L229-L237 — def test_row_deleted_without_sending_realtime_update( mock_broadcast_to_channel_group, data_fixture )
- test_row_orders_recalculated · function · L242-L251 — def test_row_orders_recalculated(mock_broadcast_to_channel_group, data_fixture)
- test_rows_history_updated · function · L258-L386 — def test_rows_history_updated( mock_broadcast_channel_group, mock_broadcast_many_channel_group, data_fixture )
- test_rows_ai_values_generation_error · function · L391-L416 — def test_rows_ai_values_generation_error(mock_broadcast_to_channel_group, data_fixture)
- test_rows_ai_values_generation_error_with_empty_rows · function · L421-L445 — def test_rows_ai_values_generation_error_with_empty_rows( mock_broadcast_to_channel_group, data_fixture )
