# backend/src/jadawel/api/mixins.py

- UnknownFieldRaisesExceptionSerializerMixin · class · L13-L63 — class UnknownFieldRaisesExceptionSerializerMixin
- __init__ · method · L19-L21 — def __init__(self, *args, **kwargs)
- to_internal_value · method · L23-L25 — def to_internal_value(self, data)
- safe_initial_data · method · L28-L46 — def safe_initial_data(self)
- validate · method · L48-L63 — def validate(self, data)
- SearchableViewMixin · class · L66-L98 — class SearchableViewMixin
- apply_search · method · L76-L98 — def apply_search(self, search: Union[str, None], queryset: QuerySet) -> QuerySet
- SortableViewMixin · class · L101-L155 — class SortableViewMixin: # The fields that can be sorted on. # It's a mapping from the field name in the request to teh field name in the # database.
- apply_sorts_or_default_sort · method · L108-L155 — def apply_sorts_or_default_sort( self, sorts: Union[str, None], queryset: QuerySet ) -> QuerySet
- FilterableViewMixin · class · L158-L180 — class FilterableViewMixin
- apply_filters · method · L161-L180 — def apply_filters(self, query_params: QueryDict, queryset: QuerySet) -> QuerySet
