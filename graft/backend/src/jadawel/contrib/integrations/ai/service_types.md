# backend/src/jadawel/contrib/integrations/ai/service_types.py

- AIAgentServiceType · class · L27-L261 — class AIAgentServiceType(ServiceType)
- SerializedDict · class · L100-L107 — class SerializedDict(ServiceDict)
- prepare_values · method · L109-L151 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser, instance: Optional[AIAgentService] = None, ) -> Dict[str, Any]
- formulas_to_resolve · method · L153-L161 — def formulas_to_resolve( self, service: AIAgentService ) -> Generator[FormulaToResolve, None, None]
- dispatch_data · method · L163-L240 — def dispatch_data( self, service: AIAgentService, resolved_values: Dict[str, Any], dispatch_context: DispatchContext, ) -> Dict[str, Any]
- dispatch_transform · method · L242-L243 — def dispatch_transform(self, data: Dict[str, Any]) -> DispatchResult
- generate_schema · method · L245-L261 — def generate_schema( self, service: AIAgentService, allowed_fields: Optional[List[str]] = None ) -> Dict[str, Any]
