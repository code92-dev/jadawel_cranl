"""The "My dashboards" page (لوحاتي), mounted under ``/api/arabase/my-dashboards/``.

docs/MY_DASHBOARDS.md. Every endpoint acts on the requesting user's own saved
dashboards only.
"""

import os

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from arabase.api.dashboard_share.public import PUBLIC_DISPATCH_ERRORS
from arabase.api.saved_dashboards.content import (
    dispatch_saved_data_source,
    saved_dashboard_content,
)
from arabase.api.saved_dashboards.errors import (
    ERROR_SAVED_DASHBOARD_DATA_FAILED,
    ERROR_SAVED_DASHBOARD_DOES_NOT_EXIST,
    ERROR_SAVED_DASHBOARD_HAS_NO_PASSWORD,
    ERROR_SAVED_DASHBOARD_LINK_INVALID,
    ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT,
    ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED,
    ERROR_SAVED_DASHBOARD_UNAVAILABLE,
    ERROR_SAVED_DASHBOARD_UNREACHABLE,
)
from arabase.api.saved_dashboards.serializers import (
    AddDashboardLinkSerializer,
    AddWorkspaceDashboardSerializer,
    AvailableWorkspaceSerializer,
    OrderSavedDashboardsSerializer,
    SavedDashboardPasswordSerializer,
    SavedDashboardSerializer,
)
from arabase.saved_dashboards.exceptions import (
    InvalidDashboardLink,
    RemoteDispatchFailed,
    SavedDashboardDoesNotExist,
    SavedDashboardHasNoPassword,
    SavedDashboardPasswordIncorrect,
    SavedDashboardPasswordRequired,
    SavedDashboardUnavailable,
    SavedDashboardUnreachable,
)
from arabase.saved_dashboards.handler import SavedDashboardHandler
from arabase.saved_dashboards.links import parse_dashboard_link
from jadawel.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from jadawel.api.decorators import map_exceptions, validate_body
from jadawel.api.errors import ERROR_USER_NOT_IN_GROUP
from jadawel.core.exceptions import ApplicationDoesNotExist, UserNotInWorkspace

TAGS = ["Arabase my dashboards"]

READ_ERRORS = {
    SavedDashboardDoesNotExist: ERROR_SAVED_DASHBOARD_DOES_NOT_EXIST,
    SavedDashboardPasswordRequired: ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED,
    SavedDashboardUnavailable: ERROR_SAVED_DASHBOARD_UNAVAILABLE,
    SavedDashboardUnreachable: ERROR_SAVED_DASHBOARD_UNREACHABLE,
}

PASSWORD_ERRORS = {
    **READ_ERRORS,
    SavedDashboardPasswordIncorrect: ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT,
    SavedDashboardHasNoPassword: ERROR_SAVED_DASHBOARD_HAS_NO_PASSWORD,
}

SAVED_ID = OpenApiParameter(
    name="saved_dashboard_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="One of the requesting user's saved dashboards.",
)


class SavedDashboardPasswordThrottle(SimpleRateThrottle):
    """Limits password guesses through this page as the public link's own
    prompt limits them (``PublicDashboardAuthThrottle``): without it the page
    would be a way around that limit. Per user and per link or saved dashboard,
    and only requests that carry a password count."""

    scope = "arabase_saved_dashboard_password"
    rate = os.getenv("JADAWEL_DASHBOARD_AUTH_RATE", "") or "10/hour"

    def get_cache_key(self, request: Request, view) -> str | None:
        if not request.user.is_authenticated or not request.data.get("password"):
            return None
        target = view.kwargs.get("saved_dashboard_id") or _link_key(
            request.data.get("url", "")
        )
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{request.user.id}-{target}",
        }


def _link_key(url: str) -> str:
    """The link a guess is aimed at, however it is written: a query string or
    an `/auth` suffix must not make a fresh throttle bucket."""

    try:
        link = parse_dashboard_link(str(url))
    except InvalidDashboardLink:
        return "invalid"
    return f"{link.origin}|{link.slug}"


def _card(request: Request, saved) -> dict:
    state = SavedDashboardHandler().state(request.user, saved)
    return SavedDashboardSerializer(state).data


class SavedDashboardsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=TAGS,
        operation_id="list_saved_dashboards",
        description="The dashboards on the user's page, in order, with whether "
        "each can be opened now.",
        responses={200: SavedDashboardSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        states = SavedDashboardHandler().list(request.user)
        return Response(SavedDashboardSerializer(states, many=True).data)


class AvailableDashboardsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=TAGS,
        operation_id="list_available_dashboards",
        description="The dashboards of the user's workspaces, by workspace, that "
        "can be added to the page.",
        responses={200: AvailableWorkspaceSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        saved_ids = SavedDashboardHandler().saved_workspace_dashboard_ids(request.user)
        return Response(
            AvailableWorkspaceSerializer(
                [
                    {
                        "id": workspace.id,
                        "name": workspace.name,
                        "dashboards": [
                            {
                                "id": dashboard.id,
                                "name": dashboard.name,
                                "saved": dashboard.id in saved_ids,
                            }
                            for dashboard in dashboards
                        ],
                    }
                    for workspace, dashboards in SavedDashboardHandler().list_available(
                        request.user
                    )
                ],
                many=True,
            ).data
        )


class AddWorkspaceDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=TAGS,
        operation_id="add_workspace_dashboard",
        description="Adds a dashboard of one of the user's workspaces to their "
        "page. Adding it again returns the existing card.",
        request=AddWorkspaceDashboardSerializer,
        responses={200: SavedDashboardSerializer},
    )
    @map_exceptions(
        {
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    @validate_body(AddWorkspaceDashboardSerializer)
    def post(self, request: Request, data: dict) -> Response:
        saved = SavedDashboardHandler().add_from_workspace(
            request.user, data["dashboard_id"]
        )
        return Response(_card(request, saved))


class AddDashboardLinkView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (SavedDashboardPasswordThrottle,)

    @extend_schema(
        tags=TAGS,
        operation_id="add_dashboard_link",
        description=(
            "Adds a dashboard by its public link, on this server or another "
            "Jadawel server. A password protected link answers "
            "`ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED` until the password is sent "
            "along."
        ),
        request=AddDashboardLinkSerializer,
        responses={200: SavedDashboardSerializer},
    )
    @map_exceptions(
        {
            **PASSWORD_ERRORS,
            InvalidDashboardLink: ERROR_SAVED_DASHBOARD_LINK_INVALID,
        }
    )
    @validate_body(AddDashboardLinkSerializer)
    def post(self, request: Request, data: dict) -> Response:
        saved = SavedDashboardHandler().add_link(
            request.user, data["url"], data["password"] or None
        )
        return Response(_card(request, saved))


class SavedDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[SAVED_ID],
        tags=TAGS,
        operation_id="remove_saved_dashboard",
        description="Takes the dashboard off the page. The dashboard itself is "
        "not touched.",
        responses={204: None},
    )
    @map_exceptions(READ_ERRORS)
    def delete(self, request: Request, saved_dashboard_id: int) -> Response:
        SavedDashboardHandler().remove(request.user, saved_dashboard_id)
        return Response(status=HTTP_204_NO_CONTENT)


class SavedDashboardPasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (SavedDashboardPasswordThrottle,)

    @extend_schema(
        parameters=[SAVED_ID],
        tags=TAGS,
        operation_id="enter_saved_dashboard_password",
        description="Opens a saved link again after its owner changed the password.",
        request=SavedDashboardPasswordSerializer,
        responses={200: SavedDashboardSerializer},
    )
    @map_exceptions(PASSWORD_ERRORS)
    @validate_body(SavedDashboardPasswordSerializer)
    def post(self, request: Request, data: dict, saved_dashboard_id: int):
        handler = SavedDashboardHandler()
        saved = handler.enter_password(
            request.user,
            handler.get(request.user, saved_dashboard_id),
            data["password"],
        )
        return Response(_card(request, saved))


class OrderSavedDashboardsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=TAGS,
        operation_id="order_saved_dashboards",
        description="Puts the page's dashboards in the given order.",
        request=OrderSavedDashboardsSerializer,
        responses={204: None},
    )
    @transaction.atomic
    @validate_body(OrderSavedDashboardsSerializer)
    def post(self, request: Request, data: dict) -> Response:
        SavedDashboardHandler().order(request.user, data["saved_dashboard_ids"])
        return Response(status=HTTP_204_NO_CONTENT)


class SavedDashboardContentView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[SAVED_ID],
        tags=TAGS,
        operation_id="get_saved_dashboard_content",
        description=(
            "The dashboard, its widgets and its data sources, shaped as a public "
            "dashboard's. The data itself comes per data source from the "
            "dispatch endpoint."
        ),
    )
    @map_exceptions(READ_ERRORS)
    def get(self, request: Request, saved_dashboard_id: int) -> Response:
        saved = SavedDashboardHandler().get(request.user, saved_dashboard_id)
        return Response(saved_dashboard_content(request, saved))


class SavedDashboardDispatchView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            SAVED_ID,
            OpenApiParameter(
                name="data_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="A data source of the saved dashboard.",
            ),
        ],
        tags=TAGS,
        operation_id="dispatch_saved_dashboard_data_source",
        description="Dispatches one data source of a saved dashboard.",
        request=None,
    )
    @map_exceptions(
        {
            **PUBLIC_DISPATCH_ERRORS,
            **READ_ERRORS,
            RemoteDispatchFailed: ERROR_SAVED_DASHBOARD_DATA_FAILED,
        }
    )
    def post(
        self, request: Request, saved_dashboard_id: int, data_source_id: int
    ) -> Response:
        saved = SavedDashboardHandler().get(request.user, saved_dashboard_id)
        return Response(dispatch_saved_data_source(request, saved, data_source_id))
