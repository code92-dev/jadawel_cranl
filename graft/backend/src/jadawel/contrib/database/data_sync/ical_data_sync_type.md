# backend/src/jadawel/contrib/database/data_sync/ical_data_sync_type.py

- UIDICalCalendarDataSyncProperty · class · L17-L22 — class UIDICalCalendarDataSyncProperty(DataSyncProperty)
- to_jadawel_field · method · L21-L22 — def to_jadawel_field(self) -> TextField
- DateStartICalCalendarDataSyncProperty · class · L25-L38 — class DateStartICalCalendarDataSyncProperty(DataSyncProperty)
- to_jadawel_field · method · L28-L35 — def to_jadawel_field(self) -> DateField
- is_equal · method · L37-L38 — def is_equal(self, jadawel_row_value: Any, data_sync_row_value: Any) -> bool
- DateEndICalCalendarDataSyncProperty · class · L41-L54 — class DateEndICalCalendarDataSyncProperty(DataSyncProperty)
- to_jadawel_field · method · L44-L51 — def to_jadawel_field(self) -> DateField
- is_equal · method · L53-L54 — def is_equal(self, jadawel_row_value: Any, data_sync_row_value: Any) -> bool
- SummaryICalCalendarDataSyncProperty · class · L57-L61 — class SummaryICalCalendarDataSyncProperty(DataSyncProperty)
- to_jadawel_field · method · L60-L61 — def to_jadawel_field(self) -> TextField
- ICalCalendarDataSyncType · class · L64-L118 — class ICalCalendarDataSyncType(DataSyncType)
- get_properties · method · L71-L77 — def get_properties(self, instance) -> List[DataSyncProperty]
- get_all_rows · method · L79-L118 — def get_all_rows( self, instance, progress_builder: Optional[ChildProgressBuilder] = None, ) -> List[Dict]: # The progress bar is difficult to setup because there are only three steps # that must completed. We're therefore using working with a total of three # because it gives some sense of what's going on.
