"""Actor checks, audit logging and invitation helpers shared by every handler.

This is the lowest layer of the organization handlers: it imports no other
handler module.
"""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel.core.models import Workspace, WorkspaceUser

from .models import (
    Organization,
    OrganizationAuditEvent,
    OrganizationMembership,
    OrganizationWorkspace,
)

User = get_user_model()


def reject_legacy_workspace_membership_mutation(
    actor: Any,
    workspace: Workspace,
    operation: str,
    target_user: Any | None = None,
) -> None:
    """Keep legacy workspace invitation flows out of managed workspaces.

    Organization membership and workspace assignments are the source of truth once a
    workspace is bound.  The core invitation handlers are still used by unmanaged
    workspaces, so the check is deliberately scoped to an existing organization
    binding and does not alter the normal Jadawel path elsewhere.
    """

    if OrganizationWorkspace.objects.filter(workspace=workspace).exists():
        from jadawel.core.exceptions import PermissionDenied

        raise PermissionDenied(actor)


def _require_actor(actor: Any) -> None:
    if not actor or not actor.is_authenticated or not actor.is_active:
        raise PermissionDenied()


def _membership(organization: Organization, user: Any) -> OrganizationMembership:
    try:
        return OrganizationMembership.objects.get(
            organization=organization, user_id=user.pk
        )
    except OrganizationMembership.DoesNotExist as exc:
        raise PermissionDenied("organization_membership_required") from exc


def _can_manage(
    actor: Any, organization: Organization
) -> OrganizationMembership | None:
    _require_actor(actor)
    if actor.is_staff:
        return None
    membership = _membership(organization, actor)
    if membership.suspended or membership.role not in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
    }:
        raise PermissionDenied("organization_admin_required")
    if organization.status != Organization.Status.ACTIVE:
        raise ValidationError({"organization": "inactive"})
    if organization.provisioning_status != Organization.ProvisioningStatus.READY:
        raise ValidationError({"organization": "provisioning_pending"})
    return membership


def audit(
    actor: Any,
    organization: Organization,
    action: str,
    target: Any,
    details: dict[str, Any],
) -> None:
    OrganizationAuditEvent.objects.create(
        actor=actor,
        organization=organization,
        action=action,
        target=str(target),
        details=details,
    )


def _pending_owner_invitations(organization: Organization):
    """Owner setup invitations that are neither accepted nor revoked."""
    return organization.invitations.filter(
        role=OrganizationMembership.Role.OWNER,
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    )


def _invitation_expires_at():
    return timezone.now() + timedelta(
        days=max(1, int(getattr(settings, "JADAWEL_ORGANIZATION_INVITATION_DAYS", 7)))
    )


def _require_workspace_admin(actor: Any, workspace: Workspace) -> None:
    """Require explicit workspace administration before binding existing data."""
    if actor.is_staff:
        return
    if not WorkspaceUser.objects.filter(
        workspace=workspace, user=actor, permissions="ADMIN"
    ).exists():
        raise PermissionDenied("workspace_admin_required")
