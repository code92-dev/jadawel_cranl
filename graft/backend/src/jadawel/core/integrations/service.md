# backend/src/jadawel/core/integrations/service.py

- IntegrationService · class · L29-L240 — class IntegrationService
- __init__ · method · L30-L31 — def __init__(self)
- get_integration · method · L33-L52 — def get_integration(self, user: AbstractUser, integration_id: int) -> Integration
- get_integrations · method · L54-L81 — def get_integrations( self, user: AbstractUser, application: Application ) -> List[Integration]
- create_integration · method · L83-L134 — def create_integration( self, user: AbstractUser, integration_type: IntegrationType, application: Application, before: Optional[Integration] = None, **kwargs, ) -> Integration
- update_integration · method · L136-L165 — def update_integration( self, user: AbstractUser, integration: IntegrationForUpdate, **kwargs ) -> Integration
- delete_integration · method · L167-L188 — def delete_integration(self, user: AbstractUser, integration: IntegrationForUpdate)
- move_integration · method · L190-L230 — def move_integration( self, user: AbstractUser, integration: IntegrationForUpdate, before: Optional[Integration] = None, ) -> Integration
- recalculate_full_orders · method · L232-L240 — def recalculate_full_orders(self, user: AbstractUser, application: Application)
