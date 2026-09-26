from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from arabase.api.activity import DEFAULT_DAYS, MAX_DAYS, get_workspace_activity
from arabase.api.database_stats import get_database_stats, visible_tables
from jadawel.api.decorators import map_exceptions
from jadawel.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from jadawel.api.schemas import get_error_schema
from jadawel.contrib.database.models import Database
from jadawel.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from jadawel.core.service import CoreService


def _visible_workspace_databases(request: Request, workspace_id: int):
    """`(workspace, databases)`: the workspace and the databases the user may see.

    Raises `WorkspaceDoesNotExist` or `UserNotInWorkspace`, which both calling
    views map to their API errors.
    """

    workspace = CoreService().get_workspace(request.user, workspace_id)

    # `list_applications_in_workspace` applies the permission filtering, so a
    # user only ever gets numbers for databases they are allowed to see. It
    # returns specific instances by default, so the isinstance check is enough
    # to drop the non-database application types.
    applications = CoreService().list_applications_in_workspace(request.user, workspace)
    databases = [a for a in applications if isinstance(a, Database)]

    return workspace, databases


class WorkspaceDatabaseStatsView(APIView):
    """Row/field/table counters for every database the user can see in a workspace.

    Kept out of the application payload on purpose. That payload is fetched on
    every page load (the sidebar depends on it), while these counters are only
    needed by the workspace home page — folding them in would make row counting a
    cost of app bootstrap for every user on every route.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the counters for databases in this workspace.",
            )
        ],
        tags=["Jadawel"],
        operation_id="workspace_database_stats",
        description=(
            "Returns the table, field and row counts of every database in the "
            "workspace that the authenticated user has access to. `row_count` is "
            "null and `rows_exact` is false when the workspace holds more tables "
            "than the endpoint will count in one pass."
        ),
        responses={
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request: Request, workspace_id: int) -> Response:
        workspace, databases = _visible_workspace_databases(request, workspace_id)

        tables = visible_tables(request.user, workspace, databases)

        return Response(get_database_stats(databases, tables))


class WorkspaceActivityView(APIView):
    """Rows created per day across a workspace, for the home page activity chart.

    Separate from the counters endpoint even though both walk the same tables:
    the counters are cheap enough to block the cards on, while this one groups as
    well as counts. Keeping them apart means a workspace large enough to make the
    activity query slow still gets its counters promptly.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the activity series for this workspace.",
            ),
            OpenApiParameter(
                name="days",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description=(
                    f"Length of the window in days, clamped to 1..{MAX_DAYS}. "
                    f"Defaults to {DEFAULT_DAYS}."
                ),
            ),
        ],
        tags=["Jadawel"],
        operation_id="workspace_activity",
        description=(
            "Returns the number of rows created per day across every database in "
            "the workspace that the authenticated user has access to. The series "
            "is dense — quiet days are present with a count of zero — and ordered "
            "oldest first. `complete` is false, and `series` empty, when the "
            "workspace holds more tables than the endpoint will scan in one pass."
        ),
        responses={
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request: Request, workspace_id: int) -> Response:
        workspace, databases = _visible_workspace_databases(request, workspace_id)

        # A non-numeric `days` is a malformed request, not a reason to 500; fall
        # back to the default and let `get_workspace_activity` clamp the range.
        try:
            days = int(request.GET.get("days", DEFAULT_DAYS))
        except (TypeError, ValueError):
            days = DEFAULT_DAYS

        tables = visible_tables(request.user, workspace, databases)

        return Response(get_workspace_activity(tables, days))
