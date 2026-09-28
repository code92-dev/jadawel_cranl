from typing import cast

from django.core.files.storage import Storage
from django.db import transaction
from django.db.transaction import Atomic
from django.urls import include, path

from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.models import Dashboard
from jadawel.contrib.dashboard.types import DashboardDict
from jadawel.contrib.dashboard.widgets.handler import WidgetHandler
from jadawel.contrib.dashboard.widgets.models import (
    GRID_COLUMNS,
    LEGACY_GRID_COLUMNS,
    rescale_serialized_widgets,
)
from jadawel.contrib.integrations.local_jadawel.integration_types import (
    LocalJadawelIntegrationType,
)
from jadawel.core.integrations.handler import IntegrationHandler
from jadawel.core.integrations.registries import integration_type_registry
from jadawel.core.models import Application, Workspace
from jadawel.core.registries import ApplicationType, ImportExportConfig
from jadawel.core.storage import ExportZipFile
from jadawel.core.trash.handler import TrashHandler
from jadawel.core.utils import ChildProgressBuilder


class DashboardApplicationType(ApplicationType):
    type = "dashboard"
    model_class = Dashboard
    serializer_field_names = ["name", "description"]
    allowed_fields = ["description"]
    supports_integrations = True

    def get_api_urls(self):
        from .api import urls as api_urls

        return [
            path("dashboard/", include(api_urls, namespace=self.type)),
        ]

    def export_safe_transaction_context(self, application: Application) -> Atomic:
        return transaction.atomic()

    def init_application(self, user, application: "Application") -> None:
        IntegrationHandler().create_integration(
            integration_type=integration_type_registry.get(
                LocalJadawelIntegrationType.type
            ),
            application=application,
            authorized_user=user,
        )

    def pre_delete(self, dashboard):
        """
        When a dashboard application is being deleted, delete
        all widgets first.
        """

        widgets = dashboard.widget_set(manager="objects_and_trash").all()

        for widget in widgets:
            TrashHandler.permanently_delete(widget)

    def export_serialized(
        self,
        dashboard: Dashboard,
        import_export_config: ImportExportConfig,
        files_zip: ExportZipFile | None = None,
        storage: Storage | None = None,
        progress_builder: ChildProgressBuilder | None = None,
    ) -> DashboardDict:
        """
        Exports the dashboard application type to a serialized format that can later
        be imported via the `import_serialized`.
        """

        self.cache = {}

        serialized_integrations = [
            IntegrationHandler().export_integration(
                i,
                files_zip=files_zip,
                storage=storage,
                cache=self.cache,
            )
            for i in IntegrationHandler().get_integrations(dashboard)
        ]

        widgets = WidgetHandler().get_widgets(dashboard)

        serialized_widgets = [
            WidgetHandler().export_widget(
                widget, files_zip=files_zip, storage=storage, cache=self.cache
            )
            for widget in widgets
        ]

        data_sources = DashboardDataSourceHandler().get_data_sources(dashboard)

        serialized_data_sources = [
            DashboardDataSourceHandler().export_data_source(
                data_source, files_zip=files_zip, storage=storage, cache=self.cache
            )
            for data_source in data_sources
        ]

        serialized_dashboard = super().export_serialized(
            dashboard,
            import_export_config,
            files_zip=files_zip,
            storage=storage,
            progress_builder=progress_builder,
        )

        return DashboardDict(
            description=dashboard.description,
            widget_grid_columns=GRID_COLUMNS,
            integrations=serialized_integrations,
            data_sources=serialized_data_sources,
            widgets=serialized_widgets,
            **serialized_dashboard,
        )

    def import_serialized(
        self,
        workspace: Workspace,
        serialized_values: dict[str, any],
        import_export_config: ImportExportConfig,
        id_mapping: dict[str, dict[int, int]],
        files_zip: ExportZipFile | None = None,
        storage: Storage | None = None,
        cache: dict[str, any] | None = None,
        progress_builder: ChildProgressBuilder | None = None,
    ) -> Application:
        """
        Imports a dashboard application exported by the `export_serialized` method.
        """

        self.cache = {}
        serialized_integrations = serialized_values.pop("integrations")
        serialized_data_sources = serialized_values.pop("data_sources")
        serialized_widgets = rescale_serialized_widgets(
            serialized_values.pop("widgets"),
            serialized_values.pop("widget_grid_columns", LEGACY_GRID_COLUMNS),
        )

        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        application_progress = progress.create_child_builder(represents_progress=20)
        integrations_progress = progress.create_child(
            represents_progress=20, total=len(serialized_integrations)
        )
        data_source_progress = progress.create_child(
            represents_progress=30, total=len(serialized_data_sources)
        )
        widgets_progress = progress.create_child(
            represents_progress=30, total=len(serialized_widgets)
        )

        application = super().import_serialized(
            workspace,
            serialized_values,
            import_export_config,
            id_mapping,
            files_zip,
            storage,
            application_progress,
        )

        if description := serialized_values.pop("description", ""):
            application.description = description
            application.save()

        for serialized_integration in serialized_integrations:
            IntegrationHandler().import_integration(
                application,
                serialized_integration,
                id_mapping,
                cache=self.cache,
                files_zip=files_zip,
                storage=storage,
            )
            integrations_progress.increment()

        for serialized_data_source in serialized_data_sources:
            DashboardDataSourceHandler().import_data_source(
                cast(Dashboard, application),
                serialized_data_source,
                id_mapping,
                files_zip,
                storage,
                self.cache,
            )
            data_source_progress.increment()

        for serialized_widget in serialized_widgets:
            WidgetHandler().import_widget(
                cast(Dashboard, application),
                serialized_widget,
                id_mapping,
                files_zip,
                storage,
                self.cache,
            )
            widgets_progress.increment()

        return application
