# backend/src/jadawel/core/integrations/handler.py

- IntegrationHandler · class · L24-L284 — class IntegrationHandler
- get_integration · method · L25-L61 — def get_integration( self, integration_id: int, base_queryset: Optional[QuerySet] = None, specific=True, ) -> Integration
- get_integration_for_update · method · L63-L84 — def get_integration_for_update( self, integration_id: int, base_queryset: Optional[QuerySet] = None ) -> IntegrationForUpdate
- get_integrations · method · L86-L121 — def get_integrations( self, application: Optional[Application] = None, base_queryset: Optional[QuerySet] = None, specific: bool = True, ) -> Union[QuerySet[Integration], Iterable[Integration]]
- per_content_type_queryset_hook · function · L111-L113 — def per_content_type_queryset_hook(model, queryset)
- create_integration · method · L123-L168 — def create_integration( self, integration_type: IntegrationType, application: Application, before=None, **kwargs, ) -> Integration
- delete_integration · method · L170-L177 — def delete_integration(self, integration: Integration)
- update_integration · method · L179-L204 — def update_integration( self, integration_type: IntegrationType, integration: IntegrationForUpdate, **kwargs, ) -> Integration
- move_integration · method · L206-L229 — def move_integration( self, integration: IntegrationForUpdate, before: Optional[Integration] = None ) -> Integration
- recalculate_full_orders · method · L231-L242 — def recalculate_full_orders( self, application: Application, )
- export_integration · method · L244-L258 — def export_integration( self, integration: Integration, import_export_config: Optional[ImportExportConfig] = None, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, )
- import_integration · method · L260-L284 — def import_integration( self, application, serialized_integration, id_mapping, cache: Optional[Dict] = None, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, )
