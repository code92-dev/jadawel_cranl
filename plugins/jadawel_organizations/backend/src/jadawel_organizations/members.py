"""Organization membership: invitations, adding, updating and removing members.

Builds on access.py, workspace_access.py and provisioning.py.
"""

import secrets
from typing import Any

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from jadawel_billing.entitlements import get_effective_entitlements, lock_capacity
from rest_framework.exceptions import PermissionDenied, ValidationError

from .access import (
    _can_manage,
    _invitation_expires_at,
    _pending_owner_invitations,
    _require_actor,
    audit,
)
from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationWorkspace,
    OrganizationWorkspaceAccess,
)
from .provisioning import team_occupied_seats
from .workspace_access import (
    _grant_owner_workspace_admin,
    _remove_workspace_user,
    _sync_member,
)


@transaction.atomic
def invite_member(
    actor: Any, organization: Organization, *, email: str, role: str = "member"
) -> tuple[OrganizationInvitation, str]:
    manager = _can_manage(actor, organization)
    email = email.strip().lower()
    if role == OrganizationMembership.Role.OWNER:
        raise ValidationError({"role": "use_owner_transfer"})
    if role not in {
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.MEMBER,
    }:
        raise ValidationError({"role": "invalid"})
    if (
        manager is not None
        and manager.role == OrganizationMembership.Role.ADMIN
        and role == OrganizationMembership.Role.ADMIN
    ):
        raise PermissionDenied("owner_required_for_admin_role")
    if OrganizationMembership.objects.filter(
        organization=organization, user__email__iexact=email
    ).exists():
        raise ValidationError({"email": "already_member"})
    OrganizationInvitation.objects.filter(
        organization=organization,
        email__iexact=email,
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    raw_token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=email,
        invited_by=actor,
        role=role,
        token_hash=OrganizationInvitation.hash_token(raw_token),
        expires_at=_invitation_expires_at(),
    )
    audit(
        actor,
        organization,
        "member.invited",
        invitation.pk,
        {"email": email, "role": role},
    )
    transaction.on_commit(
        lambda: send_mail(
            f"Invitation to {organization.name}",
            f"Use this invitation token to join: {raw_token}",
            None,
            [email],
            fail_silently=True,
        )
    )
    return invitation, raw_token


@transaction.atomic
def add_member(
    actor: Any,
    organization: Organization,
    *,
    user: Any,
    role: str = "member",
) -> OrganizationMembership:
    """Add an existing user without creating a second identity."""
    manager = _can_manage(actor, organization)
    if role not in {
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.MEMBER,
    }:
        raise ValidationError({"role": "invalid"})
    if not user.is_active:
        raise ValidationError({"user": "inactive"})
    if (
        manager is not None
        and manager.role == OrganizationMembership.Role.ADMIN
        and role == OrganizationMembership.Role.ADMIN
    ):
        raise PermissionDenied("owner_required_for_admin_role")
    with lock_capacity(organization.billing_account_id) as account:
        entitlement = get_effective_entitlements(account.pk)
        membership, created = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={"role": role},
        )
        if not created:
            if not membership.suspended:
                raise ValidationError({"user": "already_member"})
            membership.role = role
            membership.suspended = False
        used = team_occupied_seats(organization.billing_account_id)
        if used > entitlement["seat_limit"]:
            if created:
                membership.delete()
            raise ValidationError({"seat_limit": "capacity_exceeded"})
        membership.save(update_fields=["role", "suspended", "updated_at"])
    _sync_member(membership)
    audit(
        actor,
        organization,
        "member.added",
        membership.pk,
        {"user": user.pk, "role": role},
    )
    return membership


@transaction.atomic
def revoke_invitation(
    actor: Any, organization: Organization, invitation: OrganizationInvitation
) -> None:
    _can_manage(actor, organization)
    if invitation.organization_id != organization.pk:
        raise ValidationError({"invitation": "organization_mismatch"})
    if invitation.accepted_at is None and invitation.revoked_at is None:
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at"])
        audit(actor, organization, "member.invitation_revoked", invitation.pk, {})


@transaction.atomic
def accept_invitation(actor: Any, raw_token: str) -> OrganizationMembership:
    _require_actor(actor)
    invitation = (
        OrganizationInvitation.objects.select_for_update()
        .select_related("organization")
        .filter(token_hash=OrganizationInvitation.hash_token(raw_token))
        .first()
    )
    if invitation is None or invitation.accepted_at or invitation.revoked_at:
        raise ValidationError({"token": "invalid_or_replayed"})
    if invitation.expires_at <= timezone.now():
        raise ValidationError({"token": "expired"})
    if actor.email.casefold() != invitation.email.casefold():
        raise PermissionDenied("invitation_email_mismatch")
    organization = Organization.objects.select_for_update().get(
        pk=invitation.organization_id
    )
    if organization.status != Organization.Status.ACTIVE:
        raise ValidationError({"organization": "inactive"})
    with lock_capacity(organization.billing_account_id) as account:
        entitlement = get_effective_entitlements(account.pk)
        used = OrganizationMembership.objects.filter(organization=organization).count()
        pending_owner_reservation = _pending_owner_invitations(organization).count()
        membership = OrganizationMembership.objects.filter(
            organization=organization, user=actor
        ).first()
        is_owner_setup = invitation.role == OrganizationMembership.Role.OWNER
        # Owner setup replaces its reserved seat; accepting an ordinary invite
        # must leave that reservation intact.
        effective_used = used + pending_owner_reservation - int(is_owner_setup)
        if membership is None and effective_used >= entitlement["seat_limit"]:
            raise ValidationError({"seat_limit": "capacity_exceeded"})
        if (
            membership is not None
            and membership.suspended
            and effective_used > entitlement["seat_limit"]
        ):
            raise ValidationError({"seat_limit": "capacity_exceeded"})
        membership, _ = OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=actor,
            defaults={"role": invitation.role},
        )
        if membership.suspended or is_owner_setup:
            membership.suspended = False
            membership.role = invitation.role
            membership.save(update_fields=["suspended", "role", "updated_at"])
        if is_owner_setup:
            organization.owner_id = actor.pk
            organization.provisioning_status = Organization.ProvisioningStatus.READY
            organization.save(
                update_fields=["owner_id", "provisioning_status", "updated_at"]
            )
            _grant_owner_workspace_admin(organization, membership)
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at"])
    _sync_member(membership)
    audit(actor, organization, "member.accepted", membership.pk, {"email": actor.email})
    return membership


@transaction.atomic
def update_member(
    actor: Any,
    organization: Organization,
    membership: OrganizationMembership,
    *,
    role: str | None = None,
    suspended: bool | None = None,
) -> OrganizationMembership:
    _require_actor(actor)
    organization = Organization.objects.select_for_update().get(pk=organization.pk)
    if membership.organization_id != organization.pk:
        raise ValidationError({"membership": "organization_mismatch"})
    membership = OrganizationMembership.objects.select_for_update().get(
        pk=membership.pk, organization=organization
    )
    actor_membership = None if actor.is_staff else _can_manage(actor, organization)
    if role is not None:
        if role not in OrganizationMembership.Role.values:
            raise ValidationError({"role": "invalid"})
        if role == "owner":
            if not actor.is_staff and actor_membership.role != "owner":
                raise PermissionDenied("owner_transfer_requires_owner")
            if membership.suspended:
                raise ValidationError({"role": "successor_must_be_active"})
            old_owner = OrganizationMembership.objects.select_for_update().get(
                organization=organization, role="owner"
            )
            old_owner.role = "admin"
            old_owner.save(update_fields=["role", "updated_at"])
            membership.role = "owner"
            organization.owner_id = membership.user_id
            organization.save(update_fields=["owner_id", "updated_at"])
            _grant_owner_workspace_admin(organization, membership)
        elif membership.role == "owner":
            raise ValidationError({"role": "transfer_owner_first"})
        elif (
            not actor.is_staff
            and actor_membership.role == OrganizationMembership.Role.ADMIN
            and (
                membership.role == OrganizationMembership.Role.ADMIN or role == "admin"
            )
        ):
            raise PermissionDenied("owner_required_for_admin_role")
        elif role == "admin" and not actor.is_staff and membership.user_id == actor.pk:
            raise PermissionDenied("admin_cannot_self_promote")
        else:
            membership.role = role
    if suspended is not None:
        if membership.role == "owner":
            raise ValidationError({"member": "owner_cannot_be_suspended"})
        membership.suspended = suspended
    membership.save(update_fields=["role", "suspended", "updated_at"])
    _sync_member(membership)
    audit(
        actor,
        organization,
        "member.updated",
        membership.pk,
        {"role": membership.role, "suspended": membership.suspended},
    )
    return membership


@transaction.atomic
def remove_member(
    actor: Any, organization: Organization, membership: OrganizationMembership
) -> None:
    organization = Organization.objects.select_for_update().get(pk=organization.pk)
    if membership.organization_id != organization.pk:
        raise ValidationError({"membership": "organization_mismatch"})
    membership = OrganizationMembership.objects.select_for_update().get(
        pk=membership.pk, organization=organization
    )
    manager = _can_manage(actor, organization)
    if membership.role == "owner":
        raise ValidationError({"member": "owner_cannot_be_removed"})
    if (
        manager is not None
        and manager.role == OrganizationMembership.Role.ADMIN
        and membership.role == OrganizationMembership.Role.ADMIN
    ):
        raise PermissionDenied("owner_required_for_admin_role")
    for binding in OrganizationWorkspace.objects.select_related("workspace").filter(
        organization=organization
    ):
        OrganizationWorkspaceAccess.objects.filter(
            binding=binding, membership=membership
        ).delete()
        _remove_workspace_user(binding, membership)
    member_id = membership.pk
    membership.delete()
    audit(actor, organization, "member.removed", member_id, {})
