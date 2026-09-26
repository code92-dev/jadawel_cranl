"""Workspace binding and managed workspace access for organization members.

Builds on access.py only.
"""

from typing import Any

from django.db import transaction

from rest_framework.exceptions import ValidationError

from jadawel.core.models import Workspace, WorkspaceUser

from .access import _can_manage, _require_workspace_admin, audit
from .models import (
    Organization,
    OrganizationMembership,
    OrganizationWorkspace,
    OrganizationWorkspaceAccess,
)


def _sync_workspace_user(
    binding: OrganizationWorkspace,
    membership: OrganizationMembership,
    permissions: str | None = None,
) -> None:
    workspace = binding.workspace
    if membership.suspended:
        _remove_workspace_user(binding, membership, preserve_for_restore=True)
        return
    permissions = permissions or (
        "ADMIN" if membership.role in {"owner", "admin"} else "MEMBER"
    )
    workspace_user = WorkspaceUser.objects.filter(
        workspace=workspace, user=membership.user
    ).first()
    if workspace_user is None:
        order = WorkspaceUser.get_last_order(membership.user)
        WorkspaceUser.objects.create(
            workspace=workspace,
            user=membership.user,
            order=order,
            permissions=permissions,
        )
        binding.managed_user_ids = list(
            set(binding.managed_user_ids + [membership.user_id])
        )
        binding.save(update_fields=["managed_user_ids"])
    else:
        if membership.user_id not in binding.managed_user_ids:
            previous = dict(binding.managed_user_permissions)
            previous[str(membership.user_id)] = workspace_user.permissions
            binding.managed_user_ids = list(
                set(binding.managed_user_ids + [membership.user_id])
            )
            binding.managed_user_permissions = previous
            binding.save(update_fields=["managed_user_ids", "managed_user_permissions"])
        workspace_user.permissions = permissions
        workspace_user.save(update_fields=["permissions"])


def _disconnect_user_after_commit(user_id: int) -> None:
    """End active realtime sessions after managed access is revoked.

    Workspace permission checks protect subsequent requests, while the existing
    websocket consumer can otherwise keep a subscribed page open.  Schedule the
    disconnect after the transaction so a rolled-back membership change cannot
    log a user out of an unrelated session.
    """

    from jadawel.ws.tasks import force_disconnect_users

    transaction.on_commit(lambda: force_disconnect_users.delay([user_id]))


def _remove_workspace_user(
    binding: OrganizationWorkspace,
    membership: OrganizationMembership,
    *,
    preserve_for_restore: bool = False,
) -> None:
    if membership.user_id in binding.managed_user_ids:
        _disconnect_user_after_commit(membership.user_id)
        previous = dict(binding.managed_user_permissions)
        previous_permission = previous.get(str(membership.user_id))
        workspace_user = WorkspaceUser.objects.filter(
            workspace=binding.workspace, user_id=membership.user_id
        ).first()
        if preserve_for_restore:
            # Keep pre-existing workspace membership rows intact. The
            # organization permission manager still denies access while the
            # membership or organization is suspended, and unbinding/removal
            # restores the original permission below.
            if previous_permission is None and workspace_user is not None:
                workspace_user.delete()
        elif previous_permission is None:
            if workspace_user is not None:
                workspace_user.delete()
        elif workspace_user is not None:
            workspace_user.permissions = previous_permission
            workspace_user.save(update_fields=["permissions"])
        if not preserve_for_restore:
            binding.managed_user_ids = [
                uid for uid in binding.managed_user_ids if uid != membership.user_id
            ]
            previous.pop(str(membership.user_id), None)
        binding.managed_user_permissions = previous
        binding.save(update_fields=["managed_user_ids", "managed_user_permissions"])


def _sync_member(membership: OrganizationMembership) -> None:
    for binding in OrganizationWorkspace.objects.select_related("workspace").filter(
        organization=membership.organization
    ):
        access = OrganizationWorkspaceAccess.objects.filter(
            binding=binding, membership=membership
        ).first()
        if access is None:
            # Workspace access is an explicit assignment. The owner is added
            # during binding and later owners during ownership transfer.
            continue
        _sync_workspace_user(binding, membership, access.permissions)


def _grant_owner_workspace_admin(
    organization: Organization, membership: OrganizationMembership
) -> None:
    """Give an incoming owner ADMIN access to every bound workspace."""
    for binding in organization.workspaces.all():
        access, _ = OrganizationWorkspaceAccess.objects.get_or_create(
            binding=binding,
            membership=membership,
            defaults={"permissions": "ADMIN"},
        )
        if access.permissions != "ADMIN":
            access.permissions = "ADMIN"
            access.save(update_fields=["permissions"])


@transaction.atomic
def bind_workspace(
    actor: Any,
    organization: Organization,
    workspace: Workspace,
    *,
    confirm_outsiders: bool = False,
) -> OrganizationWorkspace:
    _can_manage(actor, organization)
    _require_workspace_admin(actor, workspace)
    outsiders = (
        WorkspaceUser.objects.filter(workspace=workspace)
        .exclude(user_id__in=organization.memberships.values("user_id"))
        .exists()
    )
    if outsiders:
        if not actor.is_staff:
            raise ValidationError(
                {"workspace": "unresolved_outsiders_require_general_admin"}
            )
        if not confirm_outsiders:
            raise ValidationError({"workspace": "outsiders_require_confirmation"})
    binding, created = OrganizationWorkspace.objects.get_or_create(
        organization=organization, workspace=workspace, defaults={"added_by": actor}
    )
    if not created:
        return binding
    owner_membership = (
        organization.memberships.select_related("user")
        .filter(role=OrganizationMembership.Role.OWNER, suspended=False)
        .first()
    )
    if owner_membership is not None:
        OrganizationWorkspaceAccess.objects.create(
            binding=binding, membership=owner_membership, permissions="ADMIN"
        )
        _sync_member(owner_membership)
    audit(actor, organization, "workspace.bound", workspace.pk, {})
    return binding


def workspace_binding_preview(
    actor: Any, organization: Organization, workspace: Workspace
) -> dict[str, Any]:
    _can_manage(actor, organization)
    _require_workspace_admin(actor, workspace)
    member_ids = set(organization.memberships.values_list("user_id", flat=True))
    return {
        "workspace": workspace.pk,
        "organization": organization.pk,
        "outsiders": list(
            WorkspaceUser.objects.filter(workspace=workspace)
            .exclude(user_id__in=member_ids)
            .values("user_id", "user__email", "permissions")
        ),
        "pending_invitations": list(
            organization.invitations.filter(
                accepted_at__isnull=True, revoked_at__isnull=True
            ).values("email", "role", "expires_at")
        ),
    }


@transaction.atomic
def unbind_workspace(
    actor: Any, organization: Organization, binding: OrganizationWorkspace
) -> None:
    _can_manage(actor, organization)
    if binding.organization_id != organization.pk:
        raise ValidationError({"workspace": "organization_mismatch"})
    for membership in organization.memberships.all():
        _remove_workspace_user(binding, membership)
    binding.delete()
    audit(actor, organization, "workspace.unbound", binding.workspace_id, {})


@transaction.atomic
def assign_workspace_member(
    actor: Any,
    organization: Organization,
    binding: OrganizationWorkspace,
    membership: OrganizationMembership,
    permissions: str | None = None,
) -> OrganizationWorkspaceAccess:
    _can_manage(actor, organization)
    if (
        binding.organization_id != organization.pk
        or membership.organization_id != organization.pk
    ):
        raise ValidationError({"workspace": "organization_mismatch"})
    if membership.suspended:
        raise ValidationError({"membership": "suspended"})
    if permissions is None:
        permissions = "ADMIN" if membership.role in {"owner", "admin"} else "MEMBER"
    if permissions not in {"ADMIN", "MEMBER", "VIEWER"}:
        raise ValidationError({"permissions": "invalid"})
    access, _ = OrganizationWorkspaceAccess.objects.update_or_create(
        binding=binding,
        membership=membership,
        defaults={"permissions": permissions},
    )
    _sync_workspace_user(binding, membership, permissions)
    audit(
        actor,
        organization,
        "workspace.member_assigned",
        membership.pk,
        {"workspace": binding.workspace_id},
    )
    return access


@transaction.atomic
def unassign_workspace_member(
    actor: Any,
    organization: Organization,
    binding: OrganizationWorkspace,
    membership: OrganizationMembership,
) -> None:
    """Remove one member's managed workspace access while retaining membership."""
    _can_manage(actor, organization)
    if (
        binding.organization_id != organization.pk
        or membership.organization_id != organization.pk
    ):
        raise ValidationError({"workspace": "organization_mismatch"})
    access = OrganizationWorkspaceAccess.objects.filter(
        binding=binding, membership=membership
    ).first()
    if access is None:
        raise ValidationError({"membership": "workspace_access_not_found"})
    access.delete()
    _remove_workspace_user(binding, membership)
    audit(
        actor,
        organization,
        "workspace.member_unassigned",
        membership.pk,
        {"workspace": binding.workspace_id},
    )
