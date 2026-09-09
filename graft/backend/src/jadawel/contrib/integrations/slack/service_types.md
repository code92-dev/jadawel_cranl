# backend/src/jadawel/contrib/integrations/slack/service_types.py

- SlackWriteMessageServiceType · class · L23-L174 — class SlackWriteMessageServiceType(ServiceType)
- SerializedDict · class · L34-L36 — class SerializedDict(ServiceDict)
- serializer_field_overrides · method · L39-L57 — def serializer_field_overrides(self)
- public_serializer_field_overrides · method · L60-L63 — def public_serializer_field_overrides(self): # When we're exposing this service type via a "public" serializer, # use the same overrides as usual.
- formulas_to_resolve · method · L65-L75 — def formulas_to_resolve( self, service: SlackWriteMessageService ) -> list[FormulaToResolve]
- dispatch_data · method · L77-L138 — def dispatch_data( self, service: SlackWriteMessageService, resolved_values: Dict[str, Any], dispatch_context: DispatchContext, ) -> Dict[str, Dict[str, Any]]
- dispatch_transform · method · L140-L141 — def dispatch_transform(self, data)
- get_schema_name · method · L143-L144 — def get_schema_name(self, service: SlackWriteMessageService) -> str
- generate_schema · method · L146-L174 — def generate_schema( self, service: SlackWriteMessageService, allowed_fields: Optional[List[str]] = None, ) -> Optional[Dict[str, Any]]
