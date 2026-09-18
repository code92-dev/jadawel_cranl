"""Table-scoped access for workspace guests (docs/TABLE_LEVEL_ACCESS_PLAN.md).

Jadawel's OSS permission model only knows workspace-wide roles: a
``WorkspaceUser`` row grants the whole workspace, and the richer per-scope role
system lived in the enterprise plugin this fork deletes. These two models add
the missing scope without touching a core table.

``TableGrant`` is the durable record — "this workspace member may read (or
edit) this table, and nothing else". ``PendingTableGrant`` only exists between
sending an invitation and accepting it: core's
``CoreHandler.accept_workspace_invitation`` deletes the invitation as its last
step, and the ``CASCADE`` below is what cleans these rows up once the receiver
in ``arabase.table_access.handler`` has copied them across.
"""

from django.conf import settings
from django.db import models

from jadawel.contrib.database.models import Table
from jadawel.core.mixins import CreatedAndUpdatedOnMixin
from jadawel.core.models import WorkspaceInvitation, WorkspaceUser


class TableAccessLevel(models.TextChoices):
    """What a guest may do inside a table they were granted.

    Deliberately not a role in the workspace sense: the level says nothing
    about the workspace, only about one table. Schema changes (fields, views,
    the table itself) are outside both levels — see
    ``arabase.permissions.table_grants`` for the operation allowlists.
    """

    VIEWER = "VIEWER", "Viewer"
    EDITOR = "EDITOR", "Editor"


class TableGrant(CreatedAndUpdatedOnMixin, models.Model):
    """One table a guest may reach, and at which level."""

    workspace_user = models.ForeignKey(
        WorkspaceUser,
        on_delete=models.CASCADE,
        related_name="table_grants",
        help_text="The workspace membership this grant widens.",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="guest_grants",
        help_text="The table the member is allowed to reach.",
    )
    level = models.CharField(
        max_length=16,
        choices=TableAccessLevel.choices,
        default=TableAccessLevel.VIEWER,
        help_text="Whether the member may only read the table or also edit its rows.",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        help_text="The admin who granted the access. Kept for the audit trail.",
    )

    class Meta:
        ordering = ("id",)
        unique_together = [["workspace_user", "table"]]


class PendingTableGrant(models.Model):
    """A grant promised by an invitation that has not been accepted yet."""

    invitation = models.ForeignKey(
        WorkspaceInvitation,
        on_delete=models.CASCADE,
        related_name="pending_table_grants",
        help_text="The core invitation that will materialise this grant.",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="pending_guest_grants",
        help_text="The table the invited person will be allowed to reach.",
    )
    level = models.CharField(
        max_length=16,
        choices=TableAccessLevel.choices,
        default=TableAccessLevel.VIEWER,
    )

    class Meta:
        ordering = ("id",)
        unique_together = [["invitation", "table"]]
