# backend/src/jadawel/contrib/database/views/filters.py

- sanitize_adhoc_filter_value · function · L20-L21 — def sanitize_adhoc_filter_value(value: str)
- sanitize_adhoc_filter_values · function · L24-L25 — def sanitize_adhoc_filter_values(values: Iterable[str])
- AdHocFilters · class · L29-L185 — class AdHocFilters
- from_request · method · L44-L89 — def from_request( cls, request: HttpRequest, user_field_names: bool = False, only_filter_by_field_ids: Optional[list[int]] = None, ) -> "AdHocFilters"
- deserialize_dispatch_filters · method · L92-L106 — def deserialize_dispatch_filters(cls, serialized_filters: str)
- from_dict · method · L109-L153 — def from_dict( cls, data: Dict[str, any], user_field_names: bool = False, only_filter_by_field_ids: Optional[list[int]] = None, ) -> "AdHocFilters"
- has_simple_filters · method · L156-L161 — def has_simple_filters(self)
- has_any_filters · method · L164-L165 — def has_any_filters(self)
- apply_to_queryset · method · L167-L185 — def apply_to_queryset(self, model, queryset)
