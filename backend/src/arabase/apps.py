from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class ArabaseConfig(AppConfig):
    """Root AppConfig for the Jadawel fork's additive backend code.

    ``ready()`` is the single place where we hook into Jadawel's registries
    (field types, view types, actions, plugins, permission managers, ...).
    Always prefer a registry hook here over editing a core ``jadawel.*`` file;
    if a core edit is truly unavoidable, log it in ``PATCHES.md``.
    """

    name = "arabase"
    verbose_name = "Arabase (Jadawel)"

    def ready(self):
        # Registry registrations land here as each phase is implemented, e.g.:
        #
        #     from jadawel.contrib.database.fields.registries import field_type_registry
        #     from arabase.fields.hijri import HijriDateFieldType
        #     field_type_registry.register(HijriDateFieldType())
        #
        # Keep imports inside ready() (not at module top) so Django app loading
        # order is respected.
        from arabase.plugins import ArabasePlugin
        from jadawel.core.registries import plugin_registry

        plugin_registry.register(ArabasePlugin())

        from arabase.integrations.local_jadawel.service_types import (
            LocalJadawelGroupedAggregateRowsUserServiceType,
        )
        from arabase.integrations.local_jadawel.upcoming_rows import (
            LocalJadawelUpcomingRowsUserServiceType,
        )
        from jadawel.core.services.registries import service_type_registry

        service_type_registry.register(
            LocalJadawelGroupedAggregateRowsUserServiceType()
        )
        service_type_registry.register(LocalJadawelUpcomingRowsUserServiceType())

        from arabase.dashboard.widgets.widget_types import (
            ChartWidgetType,
            ProgressWidgetType,
            RecordsListWidgetType,
            UpcomingDatesWidgetType,
        )
        from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

        widget_type_registry.register(ChartWidgetType())
        widget_type_registry.register(RecordsListWidgetType())
        widget_type_registry.register(ProgressWidgetType())
        widget_type_registry.register(UpcomingDatesWidgetType())

        from arabase.views.view_types import HtmlPageViewType
        from jadawel.contrib.database.views.registries import view_type_registry

        # Registering is all it takes to mount /api/database/views/html-page/:
        # core builds that urlconf from `view_type_registry.api_urls`.
        view_type_registry.register(HtmlPageViewType())

        from arabase.row_coloring.decorator_types import (
            BackgroundColorDecoratorType,
            LeftBorderColorDecoratorType,
        )
        from arabase.row_coloring.value_providers import (
            ConditionalColorValueProviderType,
            SingleSelectColorValueProviderType,
        )
        from jadawel.contrib.database.views.registries import (
            decorator_type_registry,
            decorator_value_provider_type_registry,
        )

        # Row coloring: the OSS re-implementation of upstream's premium row
        # colors. Concrete decorator and value provider types plug into
        # core's decoration framework, so no core edit is needed.
        decorator_type_registry.register(BackgroundColorDecoratorType())
        decorator_type_registry.register(LeftBorderColorDecoratorType())
        decorator_value_provider_type_registry.register(
            SingleSelectColorValueProviderType()
        )
        decorator_value_provider_type_registry.register(
            ConditionalColorValueProviderType()
        )

        from arabase.template_catalog import (
            LOCAL_TEMPLATE_PATTERN,
            reconcile_local_template_catalog_after_migrate,
        )

        # This fork's six bundled templates are the authoritative local-only
        # catalog. Prevent core's broad post-migration sync from importing all
        # 150+ upstream templates, and constrain any task left in Redis by an
        # older deployment to the same local pattern.
        settings.JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = False
        settings.JADAWEL_SYNC_TEMPLATES_PATTERN = LOCAL_TEMPLATE_PATTERN

        post_migrate.connect(
            reconcile_local_template_catalog_after_migrate,
            sender=self,
            dispatch_uid="arabase_reconcile_local_template_catalog",
        )

        from arabase.mcp.page.tools import (
            CreatePageViewMcpTool,
            GetPageViewMcpTool,
            ListPageViewRevisionsMcpTool,
            ListPageViewsMcpTool,
            RestorePageViewRevisionMcpTool,
            UpdatePageViewMcpTool,
        )
        from jadawel.core.mcp.registries import mcp_tool_registry

        # How a page is authored: an AI client drives these instead of Jadawel
        # calling a model itself, so no provider credentials live in the app.
        mcp_tool_registry.register(ListPageViewsMcpTool())
        mcp_tool_registry.register(GetPageViewMcpTool())
        mcp_tool_registry.register(CreatePageViewMcpTool())
        mcp_tool_registry.register(UpdatePageViewMcpTool())
        mcp_tool_registry.register(ListPageViewRevisionsMcpTool())
        mcp_tool_registry.register(RestorePageViewRevisionMcpTool())

        from arabase.mcp.protection.actions import (
            register_content_blind_mcp_action_types,
        )
        from arabase.mcp.protection.artifact_boundary import connect_artifact_lifecycle
        from arabase.mcp.protection.contracts import (
            validate_mcp_tool_protection_contracts,
        )
        from arabase.mcp.protection.interceptor import intercept_mcp_tool_call
        from arabase.mcp.protection.lifecycle import connect_mcp_protection_lifecycle

        register_content_blind_mcp_action_types()
        connect_mcp_protection_lifecycle()
        connect_artifact_lifecycle()
        validate_mcp_tool_protection_contracts(mcp_tool_registry.get_all())
        mcp_tool_registry.register_call_interceptor(intercept_mcp_tool_call)
