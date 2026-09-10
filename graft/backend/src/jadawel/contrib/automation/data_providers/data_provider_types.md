# backend/src/jadawel/contrib/automation/data_providers/data_provider_types.py

- AutomationDataProviderType · class · L19-L19 — class AutomationDataProviderType(DataProviderType, ABC)
- PreviousNodeProviderType · class · L22-L86 — class PreviousNodeProviderType(AutomationDataProviderType)
- get_data_chunk · method · L25-L62 — def get_data_chunk( self, dispatch_context: AutomationDispatchContext, path: List[str] )
- import_path · method · L64-L86 — def import_path(self, path, id_mapping, **kwargs)
- CurrentIterationDataProviderType · class · L89-L147 — class CurrentIterationDataProviderType(AutomationDataProviderType)
- get_data_chunk · method · L92-L123 — def get_data_chunk( self, dispatch_context: AutomationDispatchContext, path: List[str] )
- import_path · method · L125-L147 — def import_path(self, path, id_mapping, **kwargs)
