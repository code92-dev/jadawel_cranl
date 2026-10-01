from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "jadawel.contrib.integrations"

    def ready(self):
        from jadawel.contrib.integrations.ai.integration_types import AIIntegrationType
        from jadawel.contrib.integrations.core.integration_types import (
            SMTPIntegrationType,
        )
        from jadawel.contrib.integrations.local_jadawel.integration_types import (
            LocalJadawelIntegrationType,
        )
        from jadawel.contrib.integrations.slack.integration_types import (
            SlackBotIntegrationType,
        )
        from jadawel.core.integrations.registries import integration_type_registry
        from jadawel.core.services.registries import service_type_registry

        integration_type_registry.register(LocalJadawelIntegrationType())
        integration_type_registry.register(SMTPIntegrationType())
        integration_type_registry.register(AIIntegrationType())
        integration_type_registry.register(SlackBotIntegrationType())

        from jadawel.contrib.integrations.local_jadawel.service_types import (
            LocalJadawelAggregateRowsUserServiceType,
            LocalJadawelDeleteRowServiceType,
            LocalJadawelGetRowUserServiceType,
            LocalJadawelListRowsUserServiceType,
            LocalJadawelRowsCreatedServiceType,
            LocalJadawelRowsDeletedServiceType,
            LocalJadawelRowsUpdatedServiceType,
            LocalJadawelUpsertRowServiceType,
        )

        service_type_registry.register(LocalJadawelGetRowUserServiceType())
        service_type_registry.register(LocalJadawelListRowsUserServiceType())
        service_type_registry.register(LocalJadawelAggregateRowsUserServiceType())
        service_type_registry.register(LocalJadawelUpsertRowServiceType())
        service_type_registry.register(LocalJadawelDeleteRowServiceType())
        service_type_registry.register(LocalJadawelRowsCreatedServiceType())
        service_type_registry.register(LocalJadawelRowsUpdatedServiceType())
        service_type_registry.register(LocalJadawelRowsDeletedServiceType())

        from jadawel.contrib.integrations.slack.service_types import (
            SlackWriteMessageServiceType,
        )

        service_type_registry.register(SlackWriteMessageServiceType())

        from jadawel.contrib.integrations.core.service_types import (
            CoreHTTPRequestServiceType,
            CoreHTTPTriggerServiceType,
            CoreIteratorServiceType,
            CorePeriodicServiceType,
            CoreResponseServiceType,
            CoreRouterServiceType,
            CoreSMTPEmailServiceType,
        )

        service_type_registry.register(CoreHTTPRequestServiceType())
        service_type_registry.register(CoreSMTPEmailServiceType())
        service_type_registry.register(CoreRouterServiceType())
        service_type_registry.register(CoreHTTPTriggerServiceType())
        service_type_registry.register(CoreIteratorServiceType())
        service_type_registry.register(CorePeriodicServiceType())
        service_type_registry.register(CoreResponseServiceType())

        from jadawel.contrib.integrations.ai.service_types import AIAgentServiceType

        service_type_registry.register(AIAgentServiceType())

        import jadawel.contrib.integrations.signals  # noqa: F403, F401
