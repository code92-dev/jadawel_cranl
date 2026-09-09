# backend/src/jadawel/contrib/integrations/ai/integration_types.py

- AIIntegrationType · class · L15-L166 — class AIIntegrationType(IntegrationType)
- SerializedDict · class · L26-L27 — class SerializedDict(IntegrationDict)
- prepare_values · method · L49-L70 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser ) -> Dict[str, Any]
- get_provider_settings · method · L72-L91 — def get_provider_settings( self, integration: AIIntegration, provider_type: str ) -> Dict[str, Any]
- is_provider_overridden · method · L93-L100 — def is_provider_overridden( self, integration: AIIntegration, provider_type: str ) -> bool
- import_serialized · method · L102-L124 — def import_serialized( self, application: Application, serialized_values: Dict[str, Any], id_mapping: Dict, files_zip=None, storage=None, cache=None, ) -> AIIntegration
- export_serialized · method · L126-L166 — def export_serialized( self, instance: AIIntegration, import_export_config=None, files_zip=None, storage=None, cache=None, )
