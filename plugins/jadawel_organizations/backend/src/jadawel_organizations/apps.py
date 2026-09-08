from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class OrganizationsConfig(AppConfig):
    name = "jadawel_organizations"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.apps import apps

        if not apps.is_installed("jadawel_billing"):
            raise ImproperlyConfigured(
                "jadawel_organizations requires the jadawel_billing plugin"
            )
        from jadawel.core.registries import plugin_registry

        from jadawel_organizations.plugins import OrganizationsPlugin
        from jadawel_organizations.handlers import (
            provision_paid_team,
            team_occupied_seats,
        )
        from jadawel_billing.entitlements import (
            register_capacity_provider,
            register_team_provisioner,
        )
        from jadawel.core.registries import permission_manager_type_registry
        from jadawel_organizations.permissions import OrganizationPermissionManagerType

        plugin_registry.register(OrganizationsPlugin())  # type: ignore[no-untyped-call]
        register_capacity_provider(team_occupied_seats)
        register_team_provisioner(provision_paid_team)
        permission_manager_type_registry.register(OrganizationPermissionManagerType())
