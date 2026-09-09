# backend/src/jadawel/contrib/database/export/registries.py

- TableExporter · class · L13-L74 — class TableExporter(Instance, ABC)
- before_job_create · method · L22-L35 — def before_job_create(self, user, table, view, export_options)
- file_extension · method · L39-L43 — def file_extension(self) -> str
- can_export_table · method · L47-L50 — def can_export_table(self) -> bool
- supported_views · method · L54-L57 — def supported_views(self) -> List[str]
- option_serializer_class · method · L61-L66 — def option_serializer_class(self)
- queryset_serializer_class · method · L70-L74 — def queryset_serializer_class(self)
- TableExporterRegistry · class · L77-L89 — class TableExporterRegistry(Registry)
- get_option_serializer_map · method · L85-L89 — def get_option_serializer_map(self)
