# backend/src/jadawel/contrib/database/views/row_checker.py

- FilteredViewRows · class · L22-L39 — class FilteredViewRows
- all_allowed · method · L35-L36 — def all_allowed(self)
- __iter__ · method · L38-L39 — def __iter__(self)
- FilteredViewRowChecker · class · L42-L257 — class FilteredViewRowChecker
- __init__ · method · L50-L102 — def __init__( self, model: GeneratedTableModel, views_queryset: QuerySet, only_include_views_which_want_realtime_events: bool, updated_field_ids: Optional[Iterable[int]] = None, )
- _view_row_checks_can_be_cached · method · L104-L118 — def _view_row_checks_can_be_cached(self, view)
- _rows_with_visibility_flags · method · L120-L137 — def _rows_with_visibility_flags(self, row_ids, views_with_filters)
- get_filtered_views_where_row_is_visible · method · L139-L145 — def get_filtered_views_where_row_is_visible(self, row)
- get_filtered_views_where_rows_are_visible · method · L147-L257 — def get_filtered_views_where_rows_are_visible( self, rows: List[GeneratedTableModel] ) -> List[FilteredViewRows]
