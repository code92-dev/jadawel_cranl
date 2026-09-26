"""Organization creation, paid Team provisioning, owner setup and seat usage.

Builds on access.py only.
"""

import secrets
from typing import Any
from uuid import UUID

from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from jadawel_billing.grants import replace_grant
from jadawel_billing.handlers import create_account
from jadawel_billing.models import BillingAccount
from rest_framework.exceptions import PermissionDenied, ValidationError

from .access import (
    User,
    _invitation_expires_at,
    _pending_owner_invitations,
    _require_actor,
    audit,
)
from .models import Organization, OrganizationInvitation, OrganizationMembership


def team_occupied_seats(account_id: UUID) -> int:
    organization = Organization.objects.filter(billing_account_id=account_id).first()
    if organization is None:
        return 0
    # Suspension removes workspace access but keeps the purchased seat reserved.
    # A pending owner setup also reserves the owner seat until the invite is
    # accepted or revoked by a general administrator.
    return (
        organization.memberships.count()
        + _pending_owner_invitations(organization).count()
    )


@transaction.atomic
def provision_paid_team(account_id: UUID) -> None:
    """Create a paid Team organization exactly once after settlement."""
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
    _pending_owner_invitations(organization).update(revoked_at=timezone.now())
    raw_token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=email,
        invited_by=actor,
        role=OrganizationMembership.Role.OWNER,
        token_hash=OrganizationInvitation.hash_token(raw_token),
        expires_at=_invitation_expires_at(),
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
    invitation = _pending_owner_invitations(organization).first()
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
