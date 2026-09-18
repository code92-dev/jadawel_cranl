"""Creating, listing and revoking table-scoped guest access.

The invitation itself is core's: this handler asks
``CoreHandler.create_workspace_invitation`` for a normal ``WorkspaceInvitation``
carrying the ``GUEST`` role, so the emailed link, the signed token and the
accept page all keep working untouched. The only additive part is the list of
tables that ride along with it, and the receiver that turns them into real
grants the moment the invitation is accepted.
"""

from typing import Any, Dict, Iterable, List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction

from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST
from arabase.table_access.exceptions import (
    TableGrantDoesNotExist,
    TableNotInWorkspace,
)
from arabase.table_access.models import PendingTableGrant, TableAccessLevel, TableGrant
from jadawel.contrib.database.models import Table
from jadawel.core.handler import CoreHandler
from jadawel.core.models import Workspace, WorkspaceInvitation, WorkspaceUser
from jadawel.core.operations import (
    CreateInvitationsWorkspaceOperationType,
    ListInvitationsWorkspaceOperationType,
)
from jadawel.core.signals import workspace_invitation_accepted


def _tables_in_workspace(workspace: Workspace, table_ids: Iterable[int]) -> List[Table]:
    """Fetch the tables, refusing any that live outside this workspace.

    Without this check an admin of workspace A could grant a guest a table in
    workspace B, because the grant is stored against the membership rather than
    against the table's own workspace.
    """

    wanted = list(dict.fromkeys(table_ids))
    tables = list(
        Table.objects.filter(id__in=wanted).select_related("database__workspace")
    )
    found = {table.id for table in tables}
    if found != set(wanted) or any(
        table.database.workspace_id != workspace.id for table in tables
    ):
        raise TableNotInWorkspace(
            "Every table must exist and belong to the workspace of the invitation."
        )
    return tables


class TableAccessHandler:
    def invite_guest(
        self,
        user: AbstractUser,
        workspace: Workspace,
        email: str,
        tables: List[Dict[str, Any]],
        base_url: str,
    ) -> WorkspaceInvitation:
        """Invite `email` as a guest limited to `tables`.

        `tables` is a list of ``{"table_id": int, "level": "VIEWER"|"EDITOR"}``.
        """

        CoreHandler().check_permissions(
            user,
            CreateInvitationsWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )

        _tables_in_workspace(workspace, [entry["table_id"] for entry in tables])

        with transaction.atomic():
            invitation = CoreHandler().create_workspace_invitation(
                user=user,
                workspace=workspace,
                email=email,
                permissions=WORKSPACE_USER_PERMISSION_GUEST,
                base_url=base_url,
            )
            # `create_workspace_invitation` updates an existing invitation for
            # the same address rather than creating a second one, so the old
            # table list has to go with it.
            PendingTableGrant.objects.filter(invitation=invitation).delete()
            PendingTableGrant.objects.bulk_create(
                [
                    PendingTableGrant(
                        invitation=invitation,
                        table_id=entry["table_id"],
                        level=entry.get("level", TableAccessLevel.VIEWER),
                    )
                    for entry in tables
                ]
            )

        return invitation

    def list_pending_invitations(
        self, user: AbstractUser, workspace: Workspace
    ) -> List[WorkspaceInvitation]:
        CoreHandler().check_permissions(
            user,
            ListInvitationsWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )
        return list(
            WorkspaceInvitation.objects.filter(
                workspace=workspace, permissions=WORKSPACE_USER_PERMISSION_GUEST
            )
            .prefetch_related("pending_table_grants__table")
            .order_by("id")
        )

    def list_guests(
        self, user: AbstractUser, workspace: Workspace
    ) -> List[WorkspaceUser]:
        CoreHandler().check_permissions(
            user,
            ListInvitationsWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )
        return list(
            WorkspaceUser.objects.filter(
                workspace=workspace, permissions=WORKSPACE_USER_PERMISSION_GUEST
            )
            .select_related("user")
            .prefetch_related("table_grants__table")
            .order_by("id")
        )

    def set_grants(
        self,
        user: AbstractUser,
        workspace: Workspace,
        workspace_user: WorkspaceUser,
        tables: List[Dict[str, Any]],
    ) -> List[TableGrant]:
        """Replace a guest's grants with `tables`, as one atomic edit."""

        CoreHandler().check_permissions(
            user,
            CreateInvitationsWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )
        if workspace_user.workspace_id != workspace.id:
            raise TableGrantDoesNotExist("The membership is not in this workspace.")

        _tables_in_workspace(workspace, [entry["table_id"] for entry in tables])

        with transaction.atomic():
            TableGrant.objects.filter(workspace_user=workspace_user).delete()
            grants = TableGrant.objects.bulk_create(
                [
                    TableGrant(
                        workspace_user=workspace_user,
                        table_id=entry["table_id"],
                        level=entry.get("level", TableAccessLevel.VIEWER),
                        granted_by=user,
                    )
                    for entry in tables
                ]
            )
        return grants

    def revoke_guest(
        self,
        user: AbstractUser,
        workspace: Workspace,
        workspace_user: WorkspaceUser,
    ) -> None:
        """Remove a guest from the workspace entirely.

        Dropping only the grants would leave a member who can see the workspace
        and nothing in it, which reads as a broken account rather than as
        revoked access.
        """

        CoreHandler().check_permissions(
            user,
            CreateInvitationsWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )
        if workspace_user.workspace_id != workspace.id:
            raise TableGrantDoesNotExist("The membership is not in this workspace.")
        if workspace_user.permissions != WORKSPACE_USER_PERMISSION_GUEST:
            raise TableGrantDoesNotExist("That member is not a guest.")

        CoreHandler().delete_workspace_user(user, workspace_user)


def materialise_pending_grants(
    sender: Any,
    invitation: WorkspaceInvitation,
    user: AbstractUser,
    **kwargs: Any,
) -> None:
    """Turn an accepted guest invitation's pending grants into real ones.

    Core fires ``workspace_invitation_accepted`` *before* deleting the
    invitation, which is the only window in which the pending rows still exist.
    """

    if invitation.permissions != WORKSPACE_USER_PERMISSION_GUEST:
        return

    workspace_user: Optional[WorkspaceUser] = WorkspaceUser.objects.filter(
        workspace_id=invitation.workspace_id, user_id=user.id
    ).first()
    if workspace_user is None:
        return

    pending = list(PendingTableGrant.objects.filter(invitation=invitation))
    TableGrant.objects.filter(workspace_user=workspace_user).delete()
    TableGrant.objects.bulk_create(
        [
            TableGrant(
                workspace_user=workspace_user,
                table_id=entry.table_id,
                level=entry.level,
                granted_by=invitation.invited_by,
            )
            for entry in pending
        ]
    )


def connect_table_access_signals() -> None:
    workspace_invitation_accepted.connect(
        materialise_pending_grants,
        dispatch_uid="arabase_materialise_pending_table_grants",
    )
