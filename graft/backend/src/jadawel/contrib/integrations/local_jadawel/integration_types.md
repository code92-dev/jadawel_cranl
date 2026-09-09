# backend/src/jadawel/contrib/integrations/local_jadawel/integration_types.py

- LocalJadawelIntegrationType · class · L22-L194 — class LocalJadawelIntegrationType(IntegrationType)
- SerializedDict · class · L26-L27 — class SerializedDict(IntegrationDict)
- prepare_values · method · L41-L48 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- serialize_property · method · L50-L70 — def serialize_property( self, integration: Integration, prop_name: str, files_zip=None, storage=None, cache=None, )
- after_import · method · L72-L84 — def after_import( self, user: AbstractUser, instance: LocalJadawelIntegration ) -> None
- import_serialized · method · L86-L128 — def import_serialized( self, application: Application, serialized_values: Dict[str, Any], id_mapping: Dict, files_zip=None, storage=None, cache=None, ) -> LocalJadawelIntegration
- enhance_queryset · method · L130-L131 — def enhance_queryset(self, queryset)
- get_context_data · method · L133-L138 — def get_context_data(self, instance: LocalJadawelIntegration) -> Optional[Dict]
- get_local_jadawel_databases · method · L141-L194 — def get_local_jadawel_databases(integration: LocalJadawelIntegration) -> List
