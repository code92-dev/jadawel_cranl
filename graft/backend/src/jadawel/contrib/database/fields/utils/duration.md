# backend/src/jadawel/contrib/database/fields/utils/duration.py

- total_secs · function · L37-L59 — def total_secs( days: Optional[int] = None, hours: Optional[int] = None, mins: Optional[int] = None, secs: Optional[Union[int, float]] = None, ) -> float
- postgres_interval_to_seconds · function · L73-L104 — def postgres_interval_to_seconds(interval_str: str) -> Optional[float]
- rround · function · L203-L215 — def rround(value: float, ndigits: int = 0) -> int
- hours_with_days_search_expr · function · L361-L364 — def hours_with_days_search_expr(field_name)
- parse_duration_value · function · L476-L517 — def parse_duration_value(formatted_value: str, format: str) -> float
- duration_value_to_timedelta · function · L520-L565 — def duration_value_to_timedelta( value: Union[int, float, timedelta, str, None], format: str ) -> Optional[timedelta]
- prepare_duration_value_for_db · function · L568-L596 — def prepare_duration_value_for_db( value, duration_format, default_exc=ValidationError ) -> Optional[timedelta]
- format_duration_value · function · L599-L622 — def format_duration_value( duration: Optional[timedelta], duration_format ) -> Optional[str]
- tokenize_formatted_duration · function · L625-L633 — def tokenize_formatted_duration(duration_format: str) -> List[str]
- is_duration_format_conversion_lossy · function · L636-L650 — def is_duration_format_conversion_lossy(new_format, old_format)
- get_duration_search_expression · function · L653-L673 — def get_duration_search_expression(field) -> Func
- duration_value_sql_to_text · function · L676-L690 — def duration_value_sql_to_text(field: "DurationField") -> str
- text_value_sql_to_duration · function · L693-L707 — def text_value_sql_to_duration(field: "DurationField") -> str
- JadawelIntervalLoader · class · L715-L722 — class JadawelIntervalLoader(IntervalLoader)
- load · method · L721-L722 — def load(self, data)
