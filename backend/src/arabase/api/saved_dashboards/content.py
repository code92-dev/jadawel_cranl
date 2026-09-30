"""What a saved dashboard shows, in the public link's shape whatever its source.

The page renders every saved dashboard with the same read-only store, so the
three sources answer alike: ``{dashboard, widgets, data_sources}``, then one
dispatch per data source.
"""

from typing import Any

from django.db import transaction

from rest_framework.request import Request

from arabase.api.dashboard_share.public import (
    dispatch_public_data_source,
    public_dashboard_payload,
)
from arabase.api.dashboard_share.serializers import PublicDashboardSerializer
from arabase.saved_dashboards.handler import SavedDashboardHandler
from arabase.saved_dashboards.models import SavedDashboard, SavedDashboardSource
from jadawel.contrib.dashboard.api.data_sources.serializers import (
    DashboardDataSourceSerializer,
)
from jadawel.contrib.dashboard.api.widgets.serializers import WidgetSerializer
from jadawel.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from jadawel.contrib.dashboard.data_sources.exceptions import (
    DashboardDataSourceDoesNotExist,
)
from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.data_sources.service import DashboardDataSourceService
from jadawel.contrib.dashboard.widgets.registries import widget_type_registry
from jadawel.contrib.dashboard.widgets.service import WidgetService
from jadawel.core.services.registries import service_type_registry


def saved_dashboard_content(request: Request, saved: SavedDashboard) -> dict:
    """
    :raises SavedDashboardUnavailable, SavedDashboardPasswordRequired,
        SavedDashboardUnreachable: see ``SavedDashboardHandler``.
    """

    handler = SavedDashboardHandler()
    if saved.source == SavedDashboardSource.WORKSPACE:
        dashboard = handler.get_workspace_dashboard(request.user, saved)
        # The services check the user's permissions again, as the editor does.
        payload = {
            "dashboard": PublicDashboardSerializer(dashboard).data,
            "widgets": [
                widget_type_registry.get_serializer(widget, WidgetSerializer).data
                for widget in WidgetService().get_widgets(request.user, dashboard.id)
            ],
            "data_sources": [
                service_type_registry.get_serializer(
                    data_source.service,
                    DashboardDataSourceSerializer,
                    context={"data_source": data_source},
                ).data
                for data_source in DashboardDataSourceService().get_data_sources(
                    request.user, dashboard.id
                )
            ],
        }
    elif saved.source == SavedDashboardSource.LINK:
        payload = public_dashboard_payload(handler.get_link_share(saved).dashboard)
    else:
        payload = handler.call_remote(saved, lambda client, token: client.info(token))
    handler.remember(saved, payload)
    return payload


def dispatch_saved_data_source(
    request: Request, saved: SavedDashboard, data_source_id: int
) -> Any:
    """
    :raises DashboardDataSourceDoesNotExist: for a data source of another
        dashboard.
    :raises RemoteDispatchFailed: when the other server refused this one.
    """

    handler = SavedDashboardHandler()
    if saved.source == SavedDashboardSource.WORKSPACE:
        dashboard = handler.get_workspace_dashboard(request.user, saved)
        data_source = DashboardDataSourceHandler().get_data_source(data_source_id)
        if data_source.dashboard_id != dashboard.id:
            raise DashboardDataSourceDoesNotExist()
        with transaction.atomic():
            return DashboardDataSourceService().dispatch_data_source(
                request.user, data_source_id, DashboardDispatchContext(request)
            )
    if saved.source == SavedDashboardSource.LINK:
        with transaction.atomic():
            return dispatch_public_data_source(
                request, handler.get_link_share(saved), data_source_id
            )
    # No transaction around another server's answer: it may take seconds.
    return handler.call_remote(
        saved, lambda client, token: client.dispatch(token, data_source_id)
    )
