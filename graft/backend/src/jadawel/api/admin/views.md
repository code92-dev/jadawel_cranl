# backend/src/jadawel/api/admin/views.py

- APIListingView · class · L29-L186 — class APIListingView( APIView, SearchableViewMixin, SortableViewMixin, FilterableViewMixin )
- get · method · L44-L64 — def get(self, request)
- get_queryset · method · L66-L67 — def get_queryset(self, request)
- apply_ids_filter · method · L69-L91 — def apply_ids_filter(self, ids_param, queryset)
- get_serializer · method · L93-L100 — def get_serializer(self, request, *args, **kwargs)
- get_extend_schema_parameters · method · L103-L186 — def get_extend_schema_parameters( name, serializer_class, search_fields, sort_field_mapping, extra_parameters=None )
- AdminListingView · class · L189-L190 — class AdminListingView(APIListingView)
