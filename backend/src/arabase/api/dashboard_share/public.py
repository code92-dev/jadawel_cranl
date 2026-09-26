"""Anonymous endpoints behind a dashboard's public link.

Mounted under ``/api/arabase/public/dashboard/<slug>/``. Nothing here takes a
dashboard id: the slug is the only handle a visitor has, and every object it can
reach is filtered back to the dashboard that slug resolves to.
"""

import os

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from arabase.api.dashboard_share.errors import (
    ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST,
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD,
)
from arabase.api.dashboard_share.serializers import (
    PublicDashboardAuthResponseSerializer,
    PublicDashboardAuthSerializer,
    PublicDashboardDataSourceSerializer,
    PublicDashboardSerializer,
)
from arabase.dashboard.share.dispatch_context import (
    PublicDashboardDispatchContext,
    get_public_allowed_properties,
)
from arabase.dashboard.share.exceptions import (
    DashboardShareDoesNotExist,
    NoAuthorizationToPubliclySharedDashboard,
)
from arabase.dashboard.share.handler import (
    DashboardShareHandler,
    get_public_authorization_token,
)
from jadawel.api.decorators import map_exceptions, validate_body
from jadawel.api.schemas import get_error_schema
from jadawel.contrib.dashboard.api.data_sources.errors import (
    ERROR_DASHBOARD_DATA_DOES_NOT_EXIST,
    ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST,
    ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
)
from jadawel.contrib.dashboard.api.widgets.serializers import WidgetSerializer
from jadawel.contrib.dashboard.data_sources.exceptions import (
    DashboardDataSourceDoesNotExist,
    DashboardDataSourceImproperlyConfigured,
)
from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.widgets.handler import WidgetHandler
from jadawel.contrib.dashboard.widgets.registries import widget_type_registry
from jadawel.core.services.exceptions import (
    DoesNotExist,
    ServiceImproperlyConfiguredDispatchException,
)

SLUG_PARAMETER = OpenApiParameter(
    name="slug",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.STR,
    description="The slug of the publicly shared dashboard.",
)

PUBLIC_ERRORS = {
    DashboardShareDoesNotExist: ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST,
    NoAuthorizationToPubliclySharedDashboard: (
        ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD
    ),
}


class PublicDashboardInfoView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[SLUG_PARAMETER],
        tags=["Arabase dashboard sharing"],
        operation_id="get_public_dashboard",
        description=(
            "Returns everything needed to render a publicly shared dashboard: the "
            "dashboard, its widgets and its data sources. The data itself is "
            "fetched per data source through the dispatch endpoint."
        ),
        responses={
            401: get_error_schema(
                ["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD"]
            ),
            404: get_error_schema(["ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(PUBLIC_ERRORS)
    def get(self, request: Request, slug: str) -> Response:
        share = DashboardShareHandler().get_public_share_by_slug(
            slug, get_public_authorization_token(request)
        )
        dashboard = share.dashboard

        # Both handlers return lists, so they can be read again below after the
        # allow-list is built from them.
        widgets = WidgetHandler().get_widgets(dashboard)
        data_sources = DashboardDataSourceHandler().get_data_sources(dashboard)
        allowed_properties = get_public_allowed_properties(
            dashboard, widgets=widgets, data_sources=data_sources
        )

        return Response(
            {
                "dashboard": PublicDashboardSerializer(dashboard).data,
                "widgets": [
                    widget_type_registry.get_serializer(widget, WidgetSerializer).data
                    for widget in widgets
                ],
                "data_sources": [
                    PublicDashboardDataSourceSerializer(
                        data_source.service,
                        context={
                            "data_source": data_source,
                            # Narrows the schema to the columns this visitor can
                            # actually dispatch, so the field names of the rest
                            # of the table are not disclosed either.
                            "allowed_fields": allowed_properties.get(
                                data_source.service_id, []
                            ),
                        },
                    ).data
                    for data_source in data_sources
                ],
            }
        )


class PublicDashboardDispatchView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            SLUG_PARAMETER,
            OpenApiParameter(
                name="data_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The data source to dispatch.",
            ),
        ],
        tags=["Arabase dashboard sharing"],
        operation_id="dispatch_public_dashboard_data_source",
        description=(
            "Dispatches one data source of a publicly shared dashboard and returns "
            "its result."
        ),
        request=None,
        responses={
            400: get_error_schema(
                ["ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED"]
            ),
            401: get_error_schema(
                ["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD"]
            ),
            404: get_error_schema(
                [
                    "ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST",
                    "ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST",
                    "ERROR_DASHBOARD_DATA_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            **PUBLIC_ERRORS,
            DashboardDataSourceDoesNotExist: ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST,
            DashboardDataSourceImproperlyConfigured: (
                ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED
            ),
            ServiceImproperlyConfiguredDispatchException: (
                ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED
            ),
            DoesNotExist: ERROR_DASHBOARD_DATA_DOES_NOT_EXIST,
        }
    )
    def post(self, request: Request, slug: str, data_source_id: int) -> Response:
        share = DashboardShareHandler().get_public_share_by_slug(
            slug, get_public_authorization_token(request)
        )

        data_source = DashboardDataSourceHandler().get_data_source(data_source_id)
        # The slug is the only authorisation a visitor holds, so a data source
        # that belongs to a different dashboard must look like it doesn't exist.
        if data_source.dashboard_id != share.dashboard_id:
            raise DashboardDataSourceDoesNotExist()

        # A visitor is authorised to read the dashboard, which is the fields its
        # widgets display — not every column of the tables behind them. The
        # private context places no such limit, so it must not be used here.
        # Only this data source's entry is read, so only it is built.
        result = DashboardDataSourceHandler().dispatch_data_source(
            data_source,
            PublicDashboardDispatchContext(
                request,
                allowed_properties=get_public_allowed_properties(
                    share.dashboard, data_sources=[data_source]
                ),
            ),
        )
        return Response(result)


class PublicDashboardAuthThrottle(SimpleRateThrottle):
    """Per-link, per-caller limit on guessing a share password.

    Without it the only cost of a guess is one PBKDF2-SHA256 verify — which the
    server pays, not the caller, so the endpoint is both a password oracle and a
    way to burn CPU. The Traefik limiter in front does not cover this path: its
    rule matches the four `/api/user/*` credential endpoints only.

    Keyed on the slug as well as the caller so that hammering one link cannot
    lock a different visitor out of another.
    """

    scope = "arabase_public_dashboard_auth"
    rate = os.getenv("JADAWEL_DASHBOARD_AUTH_RATE", "") or "10/hour"

    def get_cache_key(self, request: Request, view) -> str:
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{view.kwargs.get('slug', '')}-{self.get_ident(request)}",
        }


class PublicDashboardAuthView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PublicDashboardAuthThrottle,)

    @extend_schema(
        parameters=[SLUG_PARAMETER],
        tags=["Arabase dashboard sharing"],
        operation_id="public_dashboard_token_auth",
        description=(
            "Exchanges the password of a protected public dashboard for a "
            "time limited token. Send it back in the "
            "`Jadawel-View-Authorization` header."
        ),
        request=PublicDashboardAuthSerializer,
        responses={
            200: PublicDashboardAuthResponseSerializer,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
            401: get_error_schema(
                ["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_DASHBOARD"]
            ),
            404: get_error_schema(["ERROR_DASHBOARD_SHARE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(PUBLIC_ERRORS)
    @validate_body(PublicDashboardAuthSerializer, return_validated=True)
    def post(self, request: Request, data: dict, slug: str) -> Response:
        handler = DashboardShareHandler()
        share = handler.get_share_by_slug(slug)

        # `check_public_password` answers True for a link that has no password,
        # so without the first clause this endpoint would mint a valid token for
        # any string at all. The link is already open to anyone holding the slug,
        # so nothing is gained by it — but an endpoint whose name is "auth"
        # should not report success for a credential it never checked.
        if not share.has_password or not share.check_public_password(data["password"]):
            raise NoAuthorizationToPubliclySharedDashboard(
                "The provided password is incorrect."
            )

        return Response(
            PublicDashboardAuthResponseSerializer(
                {"access_token": handler.encode_token(share)}
            ).data
        )
