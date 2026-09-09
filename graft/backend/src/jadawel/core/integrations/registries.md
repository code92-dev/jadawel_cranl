# backend/src/jadawel/core/integrations/registries.py

- IntegrationType · class · L20-L106 — class IntegrationType( ModelInstanceMixin[Integration], EasyImportExportMixin[IntegrationSubClass], CustomFieldsInstanceMixin, Instance, ABC, )
- enhance_queryset · method · L35-L41 — def enhance_queryset(self, queryset)
- prepare_values · method · L43-L58 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- serialize_property · method · L60-L73 — def serialize_property( self, integration: Integration, prop_name: str, files_zip=None, storage=None, cache=None, )
- import_serialized · method · L75-L91 — def import_serialized( self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict[str, Any], files_zip=None, storage=None, cache=None, ) -> IntegrationSubClass
- after_import · method · L93-L96 — def after_import(self, user: AbstractUser, instance: Integration) -> None
- get_context_data · method · L98-L106 — def get_context_data(self, instance: Integration) -> Optional[Dict]
- IntegrationTypeRegistry · class · L112-L121 — class IntegrationTypeRegistry( ModelRegistryMixin[IntegrationSubClass, IntegrationTypeSubClass], Registry[IntegrationTypeSubClass], CustomFieldsRegistryMixin, )
