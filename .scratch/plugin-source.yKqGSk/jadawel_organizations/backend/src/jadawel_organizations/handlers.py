import secrets
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel.core.models import Workspace, WorkspaceUser

from .models import (
    Organization,
    OrganizationAuditEvent,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationWorkspace,
    OrganizationWorkspaceAccess,
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


def _billing_account_for(organization: Organization):
    from jadawel_billing.entitlements import get_effective_entitlements

    return get_effective_entitlements(organization.billing_account_id)


def team_occupied_seats(account_id: UUID) -> int:
    organization = Organization.objects.filter(billing_account_id=account_id).first()
    if organization is None:
        return 0
    # Suspension removes workspace access but keeps the purchased seat reserved.
    # A pending owner setup also reserves the owner seat until the invite is
    # accepted or revoked by a general administrator.
    return (
        organization.memberships.count()
        + organization.invitations.filter(
            role=OrganizationMembership.Role.OWNER,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
        ).count()
    )


@transaction.atomic
def provision_paid_team(account_id: UUID) -> None:
    """Create a paid Team organization exactly once after settlement."""
    from jadawel_billing.models import BillingAccount

    account = BillingAccount.objects.select_for_update().get(pk=account_id)
    if account.kind != BillingAccount.Kind.TEAM:
        return
    organization = Organization.objects.filter(billing_account=account).first()
    if organization is not None:
        if organization.provisioning_status != Organization.ProvisioningStatus.READY:
            organization.provisioning_status = Organization.ProvisioningStatus.READY
            organization.provisioning_error = ""
            organization.save(
                update_fields=[
                    "provisioning_status",
                    "provisioning_error",
                    "updated_at",
                ]
            )
        return
    try:
        with transaction.atomic():
            organization = Organization.objects.create(
                billing_account=account,
                name=f"{account.responsible_user.get_username()}'s organization",
                owner=account.responsible_user,
                created_by=account.responsible_user,
                provisioning_status=Organization.ProvisioningStatus.READY,
            )
            OrganizationMembership.objects.create(
                organization=organization,
                user=account.responsible_user,
                role=OrganizationMembership.Role.OWNER,
            )
            audit(
                None,
                organization,
                "organization.provisioned",
                organization.pk,
                {"source": "paid_team"},
            )
    except Exception:
        # Payment truth stays paid; retrying settlement calls this idempotently.
        existing, _ = Organization.objects.get_or_create(
            billing_account=account,
            defaults={
                "name": f"{account.responsible_user.get_username()}'s organization",
                "owner": account.responsible_user,
                "created_by": account.responsible_user,
                "provisioning_status": Organization.ProvisioningStatus.FAILED,
                "provisioning_error": "provisioning_failed",
            },
        )
        if existing.provisioning_status != Organization.ProvisioningStatus.FAILED:
            existing.provisioning_status = Organization.ProvisioningStatus.FAILED
            existing.provisioning_error = "provisioning_failed"
            existing.save(
                update_fields=[
                    "provisioning_status",
                    "provisioning_error",
                    "updated_at",
                ]
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


def _require_workspace_admin(actor: Any, workspace: Workspace) -> None:
    """Require explicit workspace administration before binding existing data."""
    if actor.is_staff:
        return
    if not WorkspaceUser.objects.filter(
        workspace=workspace, user=actor, permissions="ADMIN"
    ).exists():
        raise PermissionDenied("workspace_admin_required")


@transaction.atomic
def create_organization(
    actor: Any,
    *,
    name: str,
    owner: Any | None = None,
    owner_email: str | None = None,
    creation_key: UUID | None = None,
    plan: Any | None = None,
    seat_limit: int | None = None,
    starts_at: Any | None = None,
    expires_at: Any | None = None,
    reason: str = "",
) -> Organization:
    _require_actor(actor)
    if not actor.is_staff:
        raise PermissionDenied("general_admin_required")
    name = name.strip()
    if not name:
        raise ValidationError({"name": "required"})
    if creation_key:
        existing = Organization.objects.filter(creation_key=creation_key).first()
        if existing:
            if existing.created_by_id != actor.pk:
                raise ValidationError({"creation_key": "already_used"})
            return existing
    if owner is None and not owner_email:
        raise ValidationError({"owner": "required"})
    if owner is not None and owner_email:
        raise ValidationError({"owner": "choose_id_or_email"})
    if owner_email:
        owner_email = owner_email.strip().lower()
        owner = User.objects.filter(email__iexact=owner_email, is_active=True).first()
        if owner is None:
            # The organization is created with a reserved owner seat and a
            # restricted setup invitation. The invitation acceptance below
            # attaches the real user without creating a second identity.
            pending_owner = True
        else:
            pending_owner = False
    else:
        pending_owner = False

    try:
        from jadawel_billing.handlers import create_account

        # Until a new owner accepts, the general administrator is the billing
        # account's responsible user. This is an internal payer reference and
        # does not grant organization data access. Keep account and organization
        # creation in a savepoint so a concurrent idempotency-key retry cannot
        # leave an orphaned Team account behind.
        with transaction.atomic():
            account = create_account(
                actor,
                kind="TEAM",
                responsible_user=owner or actor,
            )
            organization = Organization.objects.create(
                billing_account=account,
                name=name,
                owner=owner,
                created_by=actor,
                creation_key=creation_key,
                provisioning_status=(
                    Organization.ProvisioningStatus.PENDING
                    if pending_owner
                    else Organization.ProvisioningStatus.READY
                ),
            )
    except ImportError as exc:
        raise RuntimeError(
            "jadawel_organizations requires the jadawel_billing plugin"
        ) from exc
    except IntegrityError:
        if creation_key:
            existing = (
                Organization.objects.select_related("billing_account")
                .filter(creation_key=creation_key)
                .first()
            )
            if existing is not None:
                if existing.created_by_id != actor.pk:
                    raise ValidationError({"creation_key": "already_used"})
                return existing
        raise
    if owner is not None:
        OrganizationMembership.objects.create(
            organization=organization,
            user=owner,
            role=OrganizationMembership.Role.OWNER,
        )
    if plan is not None:
        from jadawel_billing.grants import replace_grant

        if seat_limit is None:
            raise ValidationError({"seat_limit": "required_with_plan"})
        if not reason.strip():
            raise ValidationError({"reason": "required_with_plan"})
        replace_grant(
            actor,
            account.pk,
            plan=plan,
            seat_limit=seat_limit,
            starts_at=starts_at or timezone.now(),
            expires_at=expires_at,
            reason=reason,
        )
    audit(
        actor,
        organization,
        "organization.created",
        organization.pk,
        {
            "name": name,
            "complimentary": True,
            "pending_owner": bool(pending_owner),
        },
    )
    if pending_owner:
        invitation, raw_token = _issue_owner_setup_invitation(
            actor, organization, owner_email
        )
        # Expose the token to the trusted admin API caller so an installation
        # can hand it to an internal onboarding system. Normal mail delivery
        # still happens after the transaction commits.
        organization._owner_setup_token = raw_token
    return organization


@transaction.atomic
def _issue_owner_setup_invitation(
    actor: Any, organization: Organization, email: str
) -> tuple[OrganizationInvitation, str]:
    """Rotate the restricted owner setup invite for an organization."""
    _require_actor(actor)
    if not actor.is_staff:
        raise PermissionDenied("general_admin_required")
    email = email.strip().lower()
    OrganizationInvitation.objects.filter(
        organization=organization,
        role=OrganizationMembership.Role.OWNER,
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    raw_token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=email,
        invited_by=actor,
        role=OrganizationMembership.Role.OWNER,
        token_hash=OrganizationInvitation.hash_token(raw_token),
        expires_at=timezone.now()
        + timedelta(
            days=max(
                1,
                int(getattr(settings, "JADAWEL_ORGANIZATION_INVITATION_DAYS", 7)),
            )
        ),
    )
    audit(
        actor,
        organization,
        "owner.setup_invited",
        invitation.pk,
        {"email": email},
    )
    transaction.on_commit(
        lambda: send_mail(
            f"Set up ownership of {organization.name}",
            f"Use this invitation token to become the organization owner: {raw_token}",
            None,
            [email],
            fail_silently=True,
        )
    )
    return invitation, raw_token


def resend_owner_setup(actor: Any, organization: Organization) -> str:
    """Resend the current owner setup invitation, rotating its token."""
    if not actor.is_staff:
        raise PermissionDenied("general_admin_required")
    invitation = organization.invitations.filter(
        role=OrganizationMembership.Role.OWNER,
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).first()
    if invitation is None:
        raise ValidationError({"owner": "no_pending_setup"})
    _, token = _issue_owner_setup_invitation(actor, organization, invitation.email)
    return token


def reassign_owner_setup(actor: Any, organization: Organization, email: str) -> str:
    """Assign a new pending owner email and rotate the setup token."""
    if not actor.is_staff:
        raise PermissionDenied("general_admin_required")
    if organization.owner_id is not None:
        raise ValidationError({"owner": "already_assigned"})
    email = email.strip().lower()
    if not email:
        raise ValidationError({"email": "required"})
    _, token = _issue_owner_setup_invitation(actor, organization, email)
    return token


@transaction.atomic
def create_pending_team(
    actor: Any, *, name: str, creation_key: UUID | None = None
) -> Organization:
    """Start a Team checkout before payment settlement.

    The account and organization are deliberately created together so the
    checkout can carry a stable account id.  Provisioning becomes ready only
    after the billing plugin verifies a paid Team order.
    """
    _require_actor(actor)
    name = name.strip()
    if not name:
        raise ValidationError({"name": "required"})

    from jadawel_billing.models import BillingAccount

    if creation_key:
        existing = (
            Organization.objects.select_related("billing_account")
            .filter(creation_key=creation_key)
            .first()
        )
        if existing is not None:
            if existing.billing_account.responsible_user_id != actor.pk:
                raise ValidationError({"creation_key": "already_used"})
            return existing

    try:
        # Keep the account and organization in one savepoint. If two retrying
        # requests race on the unique creation key, the losing account is
        # rolled back before the existing organization is returned.
        with transaction.atomic():
            account = BillingAccount.objects.create(
                kind=BillingAccount.Kind.TEAM,
                responsible_user=actor,
            )
            organization = Organization.objects.create(
                billing_account=account,
                name=name,
                owner=actor,
                created_by=actor,
                creation_key=creation_key,
                provisioning_status=Organization.ProvisioningStatus.PENDING,
            )
            OrganizationMembership.objects.create(
                organization=organization,
                user=actor,
                role=OrganizationMembership.Role.OWNER,
            )
            audit(
                actor,
                organization,
                "organization.checkout_started",
                organization.pk,
                {"name": name},
            )
            return organization
    except IntegrityError:
        if creation_key:
            existing = (
                Organization.objects.select_related("billing_account")
                .filter(creation_key=creation_key)
                .first()
            )
            if existing is not None:
                if existing.billing_account.responsible_user_id != actor.pk:
                    raise ValidationError({"creation_key": "already_used"})
                return existing
        raise


@transaction.atomic
def update_organization(
    actor: Any, organization: Organization, *, name: str
) -> Organization:
    """Update organization settings while retaining an audit trail."""
    _can_manage(actor, organization)
    name = name.strip()
    if not name:
        raise ValidationError({"name": "required"})
    if len(name) > 160:
        raise ValidationError({"name": "too_long"})
    before = organization.name
    if before == name:
        return organization
    organization.name = name
    organization.save(update_fields=["name", "updated_at"])
    audit(
        actor,
        organization,
        "organization.updated",
        organization.pk,
        {"before": {"name": before}, "after": {"name": name}},
    )
    return organization


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
        expires_at=timezone.now()
        + timedelta(
            days=max(
                1, int(getattr(settings, "JADAWEL_ORGANIZATION_INVITATION_DAYS", 7))
            )
        ),
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
    from jadawel_billing.entitlements import get_effective_entitlements, lock_capacity

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
    from jadawel_billing.entitlements import get_effective_entitlements, lock_capacity

    with lock_capacity(organization.billing_account_id) as account:
        entitlement = get_effective_entitlements(account.pk)
        used = OrganizationMembership.objects.filter(organization=organization).count()
        pending_owner_reservation = OrganizationInvitation.objects.filter(
            organization=organization,
            role=OrganizationMembership.Role.OWNER,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
        ).count()
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
            for binding in organization.workspaces.all():
                access, _ = OrganizationWorkspaceAccess.objects.get_or_create(
                    binding=binding,
                    membership=membership,
                    defaults={"permissions": "ADMIN"},
                )
                if access.permissions != "ADMIN":
                    access.permissions = "ADMIN"
                    access.save(update_fields=["permissions"])
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
    with transaction.atomic():
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
                for binding in organization.workspaces.all():
                    access, created = OrganizationWorkspaceAccess.objects.get_or_create(
                        binding=binding,
                        membership=membership,
                        defaults={"permissions": "ADMIN"},
                    )
                    if not created and access.permissions != "ADMIN":
                        access.permissions = "ADMIN"
                        access.save(update_fields=["permissions"])
            elif membership.role == "owner":
                raise ValidationError({"role": "transfer_owner_first"})
            elif (
                not actor.is_staff
                and actor_membership.role == OrganizationMembership.Role.ADMIN
                and (
                    membership.role == OrganizationMembership.Role.ADMIN
                    or role == "admin"
                )
            ):
                raise PermissionDenied("owner_required_for_admin_role")
            elif (
                role == "admin"
                and not actor.is_staff
                and membership.user_id == actor.pk
            ):
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
    with transaction.atomic():
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


def organization_snapshot(organization: Organization) -> dict[str, Any]:
    effective = _billing_account_for(organization)
    from jadawel_billing.models import Subscription

    subscription = (
        Subscription.objects.filter(account_id=organization.billing_account_id)
        .order_by("-period_start", "-id")
        .first()
    )
    pending_owner = organization.invitations.filter(
        role=OrganizationMembership.Role.OWNER,
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).first()
    return {
        "id": str(organization.pk),
        "name": organization.name,
        "status": organization.status,
        "provisioning_status": organization.provisioning_status,
        "owner": (
            {"id": organization.owner_id, "email": organization.owner.email}
            if organization.owner_id
            else None
        ),
        "pending_owner_email": pending_owner.email if pending_owner else None,
        "billing_account": str(organization.billing_account_id),
        "billing_subscription": (
            None
            if subscription is None
            else {
                "status": subscription.status,
                "period_end": subscription.period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        ),
        "members_count": organization.memberships.filter(suspended=False).count(),
        "effective_entitlement": effective,
    }


@transaction.atomic
def transition_to_personal(actor: Any, organization: Organization):
    """Safely leave Team billing after members and workspaces are resolved."""
    _require_actor(actor)
    if not actor.is_staff and organization.owner_id != actor.pk:
        raise PermissionDenied("owner_required")
    if (
        organization.workspaces.exists()
        or organization.memberships.exclude(user_id=actor.pk).exists()
    ):
        raise ValidationError({"organization": "resolve_members_and_workspaces_first"})
    from jadawel_billing.models import BillingAccount, Subscription

    if organization.invitations.filter(
        accepted_at__isnull=True, revoked_at__isnull=True
    ).exists():
        raise ValidationError({"organization": "resolve_pending_invitations_first"})
    if Subscription.objects.filter(
        account=organization.billing_account,
        status__in=[
            Subscription.Status.ACTIVE,
            Subscription.Status.GRACE,
            Subscription.Status.PAST_DUE,
        ],
        cancel_at_period_end=False,
    ).exists():
        raise ValidationError({"organization": "stop_team_renewal_first"})

    personal, _ = BillingAccount.objects.get_or_create(
        responsible_user=actor, kind=BillingAccount.Kind.INDIVIDUAL
    )
    organization.status = Organization.Status.ARCHIVED
    organization.archived_at = timezone.now()
    organization.save(update_fields=["status", "archived_at", "updated_at"])
    audit(
        actor,
        organization,
        "organization.transitioned_to_personal",
        organization.pk,
        {"personal_account": str(personal.pk)},
    )
    return personal


@transaction.atomic
def change_organization_lifecycle(
    actor: Any, organization: Organization, *, action: str
) -> Organization:
    """Change organization status and revoke or restore managed access."""
    _require_actor(actor)
    if action not in {"suspend", "reactivate", "archive"}:
        raise ValidationError({"action": "invalid"})
    if not actor.is_staff:
        membership = _membership(organization, actor)
        if membership.suspended or membership.role != OrganizationMembership.Role.OWNER:
            raise PermissionDenied("owner_required")
        if action == "archive":
            raise PermissionDenied("general_admin_required")

    status_by_action = {
        "suspend": Organization.Status.SUSPENDED,
        "reactivate": Organization.Status.ACTIVE,
        "archive": Organization.Status.ARCHIVED,
    }
    organization.status = status_by_action[action]
    organization.archived_at = timezone.now() if action == "archive" else None
    organization.save(update_fields=["status", "archived_at", "updated_at"])

    bindings = OrganizationWorkspace.objects.select_related("workspace").filter(
        organization=organization
    )
    if action in {"suspend", "archive"}:
        for binding in bindings:
            for membership in organization.memberships.all():
                _remove_workspace_user(binding, membership, preserve_for_restore=True)
    else:
        for membership in organization.memberships.select_related("user").filter(
            suspended=False
        ):
            _sync_member(membership)
    audit(actor, organization, f"organization.{action}", organization.pk, {})
    return organization
