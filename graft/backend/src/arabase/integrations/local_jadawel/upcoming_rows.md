# backend/src/arabase/integrations/local_jadawel/upcoming_rows.py

- LocalJadawelUpcomingRowsUserServiceType · class · L32-L234 — class LocalJadawelUpcomingRowsUserServiceType(LocalJadawelListRowsUserServiceType)
- allowed_fields · method · L42-L47 — def allowed_fields(self)
- serializer_field_names · method · L50-L55 — def serializer_field_names(self)
- serializer_field_overrides · method · L58-L66 — def serializer_field_overrides(self)
- SerializedDict · class · L68-L71 — class SerializedDict(LocalJadawelListRowsUserServiceType.SerializedDict)
- enhance_queryset · method · L73-L74 — def enhance_queryset(self, queryset)
- prepare_values · method · L76-L123 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser, instance: Optional[ServiceSubClass] = None, ) -> Dict[str, Any]
- _is_date_field · method · L126-L139 — def _is_date_field(field) -> bool
- export_prepared_values · method · L141-L146 — def export_prepared_values(self, instance: LocalJadawelUpcomingRows) -> dict
- deserialize_property · method · L148-L175 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: Dict[str, Any], files_zip=None, storage=None, cache=None, **kwargs, )
- resolve_service_formulas · method · L177-L192 — def resolve_service_formulas( self, service: LocalJadawelUpcomingRows, dispatch_context: DispatchContext, ) -> Dict[str, Any]
- get_table_queryset · method · L194-L234 — def get_table_queryset(self, service, table, dispatch_context, model)
