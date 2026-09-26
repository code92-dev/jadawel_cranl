"""Organization settings, snapshots and status lifecycle transitions.

Builds on access.py and workspace_access.py.
"""

from typing import Any

from django.db import transaction
from django.utils import timezone

from jadawel_billing.entitlements import get_effective_entitlements
from jadawel_billing.models import BillingAccount, Subscription
from rest_framework.exceptions import PermissionDenied, ValidationError

from .access import (
    _can_manage,
    _membership,
    _pending_owner_invitations,
    _require_actor,
    audit,
)
from .models import Organization, OrganizationMembership, OrganizationWorkspace
from .workspace_access import _remove_workspace_user, _sync_member


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


def organization_snapshot(organization: Organization) -> dict[str, Any]:
    effective = get_effective_entitlements(organization.billing_account_id)
    subscription = (
        Subscription.objects.filter(account_id=organization.billing_account_id)
        .order_by("-period_start", "-id")
        .first()
    )
    pending_owner = _pending_owner_invitations(organization).first()
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
