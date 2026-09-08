from django.apps import AppConfig


class BillingConfig(AppConfig):
    name = "jadawel_billing"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from jadawel.core.registries import plugin_registry

        from jadawel_billing.plugins import BillingPlugin

        # Core's registry base constructor does not declare parameter types.
        plugin_registry.register(BillingPlugin())  # type: ignore[no-untyped-call]
