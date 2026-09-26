"""Admin endpoints for table-scoped guest access.

Mounted under ``/api/arabase/workspace/<workspace_id>/table-access/``. Every
method needs the same permission as inviting a normal member, so the surface a
workspace admin controls does not change: only the *shape* of what an invited
person ends up seeing does.
"""

from typing import Any, Dict, Iterable, List, Union

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from arabase.api.table_access.errors import (
    ERROR_TABLE_GRANT_DOES_NOT_EXIST,
    ERROR_TABLE_NOT_IN_WORKSPACE,
)
from arabase.api.table_access.serializers import (
    InviteGuestSerializer,
    SetGrantsSerializer,
)
from arabase.table_access.exceptions import (
    TableGrantDoesNotExist,
    TableNotInWorkspace,
)
from arabase.table_access.handler import TableAccessHandler
from arabase.table_access.models import PendingTableGrant, TableGrant
from jadawel.api.decorators import map_exceptions, validate_body
from jadawel.api.errors import (
    ERROR_GROUP_DOES_NOT_EXIST,
    ERROR_HOSTNAME_IS_NOT_ALLOWED,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
    ERROR_USER_NOT_IN_GROUP,
)
from jadawel.api.schemas import get_error_schema
from jadawel.api.workspaces.users.errors import ERROR_GROUP_USER_ALREADY_EXISTS
from jadawel.core.exceptions import (
    BaseURLHostnameNotAllowed,
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
    WorkspaceUserAlreadyExists,
)
from jadawel.core.handler import CoreHandler
from jadawel.core.models import WorkspaceInvitation, WorkspaceUser

WORKSPACE_ID_PARAMETER = OpenApiParameter(
    name="workspace_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The workspace whose table guests are managed.",
)

COMMON_ERRORS = {
    WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
    UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
    UserInvalidWorkspacePermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
    TableNotInWorkspace: ERROR_TABLE_NOT_IN_WORKSPACE,
    TableGrantDoesNotExist: ERROR_TABLE_GRANT_DOES_NOT_EXIST,
}


def _serialize_tables(
    grants: Iterable[Union[TableGrant, PendingTableGrant]],
) -> List[Dict[str, Any]]:
    return [
        {
            "table_id": grant.table_id,
            "name": grant.table.name,
            "database_id": grant.table.database_id,
            "level": grant.level,
        }
        for grant in grants
    ]


def _guest_payload(
    workspace_user: WorkspaceUser, grants: Iterable[TableGrant]
) -> Dict[str, Any]:
    """A table guest as the admin API answers it.

    `grants` must already carry their table (prefetched or selected), because
    each one reads its table's name and database.
    """

    return {
        "workspace_user_id": workspace_user.id,
        "user_id": workspace_user.user_id,
        "email": workspace_user.user.email,
        "name": workspace_user.user.first_name,
        "tables": _serialize_tables(grants),
    }


def _invitation_payload(
    invitation: WorkspaceInvitation, grants: Iterable[PendingTableGrant]
) -> Dict[str, Any]:
    """A pending guest invitation as the admin API answers it.

    `grants` must already carry their table, as for `_guest_payload`.
    """

    return {
        "id": invitation.id,
        "email": invitation.email,
        "created_on": invitation.created_on,
        "tables": _serialize_tables(grants),
    }


class TableAccessView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[WORKSPACE_ID_PARAMETER],
        tags=["Arabase table access"],
        operation_id="list_table_access",
        description=(
            "Lists the workspace's table guests with the tables each of them can "
            "reach, plus the guest invitations that have not been accepted yet."
        ),
        responses={
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(COMMON_ERRORS)
    def get(self, request: Request, workspace_id: int) -> Response:
        workspace = CoreHandler().get_workspace(workspace_id)
        handler = TableAccessHandler()

        guests = handler.list_guests(request.user, workspace)
        invitations = handler.list_pending_invitations(request.user, workspace)

        return Response(
            {
                "guests": [
                    _guest_payload(workspace_user, workspace_user.table_grants.all())
                    for workspace_user in guests
                ],
                "invitations": [
                    _invitation_payload(
                        invitation, invitation.pending_table_grants.all()
                    )
                    for invitation in invitations
                ],
            }
        )

    @extend_schema(
        parameters=[WORKSPACE_ID_PARAMETER],
        tags=["Arabase table access"],
        operation_id="invite_table_guest",
        description=(
            "Invites an email address to the workspace as a guest that can only "
            "reach the given tables. The invitation, its email and the accept page "
            "are the standard workspace ones."
        ),
        request=InviteGuestSerializer,
        responses={
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_GROUP_USER_ALREADY_EXISTS",
                    "ERROR_HOSTNAME_IS_NOT_ALLOWED",
                    "ERROR_TABLE_NOT_IN_WORKSPACE",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            **COMMON_ERRORS,
            WorkspaceUserAlreadyExists: ERROR_GROUP_USER_ALREADY_EXISTS,
            BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED,
        }
    )
    @validate_body(InviteGuestSerializer, return_validated=True)
    def post(self, request: Request, workspace_id: int, data: Dict) -> Response:
        workspace = CoreHandler().get_workspace(workspace_id)
        invitation = TableAccessHandler().invite_guest(
            user=request.user,
            workspace=workspace,
            email=data["email"],
            tables=data["tables"],
            base_url=data["base_url"],
        )
        return Response(
            _invitation_payload(
                invitation, invitation.pending_table_grants.select_related("table")
            )
        )


class TableAccessGuestView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[WORKSPACE_ID_PARAMETER],
        tags=["Arabase table access"],
        operation_id="update_table_guest",
        description="Replaces the set of tables a guest can reach.",
        request=SetGrantsSerializer,
        responses={
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                    "ERROR_TABLE_NOT_IN_WORKSPACE",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_TABLE_GRANT_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(COMMON_ERRORS)
    @validate_body(SetGrantsSerializer, return_validated=True)
    def patch(
        self, request: Request, workspace_id: int, workspace_user_id: int, data: Dict
    ) -> Response:
        workspace = CoreHandler().get_workspace(workspace_id)
        workspace_user = _get_workspace_user(workspace_user_id)
        TableAccessHandler().set_grants(
            request.user, workspace, workspace_user, data["tables"]
        )
        workspace_user.refresh_from_db()
        return Response(
            _guest_payload(
                workspace_user, workspace_user.table_grants.select_related("table")
            )
        )

    @extend_schema(
        parameters=[WORKSPACE_ID_PARAMETER],
        tags=["Arabase table access"],
        operation_id="revoke_table_guest",
        description=(
            "Removes the guest from the workspace. Revoking every table but "
            "leaving the membership would show them an empty workspace instead."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_USER_INVALID_GROUP_PERMISSIONS"]
            ),
            404: get_error_schema(
                ["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_TABLE_GRANT_DOES_NOT_EXIST"]
            ),
        },
    )
    @map_exceptions(COMMON_ERRORS)
    def delete(
        self, request: Request, workspace_id: int, workspace_user_id: int
    ) -> Response:
        workspace = CoreHandler().get_workspace(workspace_id)
        workspace_user = _get_workspace_user(workspace_user_id)
        TableAccessHandler().revoke_guest(request.user, workspace, workspace_user)
        return Response(status=HTTP_204_NO_CONTENT)


def _get_workspace_user(workspace_user_id: int) -> WorkspaceUser:
    workspace_user = (
        WorkspaceUser.objects.filter(id=workspace_user_id)
        .select_related("user", "workspace")
        .first()
    )
    if workspace_user is None:
        raise TableGrantDoesNotExist("That membership does not exist.")
    return workspace_user
