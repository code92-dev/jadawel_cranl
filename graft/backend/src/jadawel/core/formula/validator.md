# backend/src/jadawel/core/formula/validator.py

- ensure_boolean · function · L18-L37 — def ensure_boolean(value: Any, strict=True) -> bool
- ensure_numeric · function · L40-L81 — def ensure_numeric( value: Any, allow_null: bool = False ) -> Optional[Union[int, float, Decimal]]
- ensure_integer · function · L84-L107 — def ensure_integer(value: Any, allow_empty: bool = False) -> Optional[int]
- ensure_string · function · L110-L134 — def ensure_string(value: Any, allow_empty: bool = True) -> str
- ensure_string_or_integer · function · L137-L150 — def ensure_string_or_integer(value: Any, allow_empty: bool = True) -> Union[int, str]
- ensure_array · function · L153-L176 — def ensure_array(value: Any, allow_empty: bool = True) -> List[Any]
- ensure_email · function · L179-L192 — def ensure_email(value: Any) -> str
- ensure_date · function · L195-L206 — def ensure_date(value: Any) -> Optional[date]
- ensure_datetime · function · L209-L221 — def ensure_datetime(value: Any) -> Optional[datetime]
- ensure_object · function · L224-L242 — def ensure_object(value: Any) -> Optional[dict]
