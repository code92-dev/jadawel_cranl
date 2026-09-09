# backend/src/jadawel/core/services/handler.py

- ServiceHandler · class · L25-L268 — class ServiceHandler
- get_service · method · L26-L61 — def get_service( self, service_id: int, base_queryset: QuerySet[Service] = None, specific=True ) -> Service
- get_service_for_update · method · L63-L82 — def get_service_for_update( self, service_id: int, base_queryset: QuerySet[Service] = None ) -> ServiceForUpdate
- get_services · method · L84-L138 — def get_services( self, integration: Optional[Integration] = None, base_queryset: Optional[QuerySet] = None, specific: bool = True, ) -> Union[QuerySet[Page], Iterable[Page]]
- per_content_type_queryset_hook · function · L107-L109 — def per_content_type_queryset_hook(model, queryset)
- create_service · method · L140-L161 — def create_service(self, service_type: ServiceType, **kwargs) -> Service
- update_service · method · L163-L197 — def update_service( self, service_type: ServiceType, service: ServiceForUpdate, **kwargs ) -> UpdatedService
- delete_service · method · L199-L208 — def delete_service(self, service_type: ServiceType, service: Service)
- dispatch_service · method · L210-L230 — def dispatch_service( self, service: Service, dispatch_context: DispatchContext, ) -> DispatchResult
- export_service · method · L232-L244 — def export_service( self, service, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, )
- import_service · method · L246-L268 — def import_service( self, integration, serialized_service, id_mapping, import_formula: Optional[Callable[[str, Dict[str, Any]], str]] = None, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, import_export_config: Optional[ImportExportConfig] = None, )
