from datetime import datetime
from typing import Any
from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from jadawel_billing.entitlements import lock_capacity, validate_capacity
from jadawel_billing.handlers import audit, require_admin
from jadawel_billing.models import ManualEntitlementGrant, Plan


def grant_snapshot(grant: ManualEntitlementGrant | None) -> dict[str, Any] | None:
    if grant is None:
        return None
    return {
        "plan": grant.plan_id,
        "seat_limit": grant.seat_limit,
        "starts_at": grant.starts_at.isoformat(),
        "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
        "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        "revision": grant.revision,
        "reason": grant.reason,
    }


def replace_grant(
    actor: Any,
    account_id: UUID,
    *,
    plan: Plan,
    seat_limit: int,
    starts_at: datetime,
    expires_at: datetime | None = None,
    reason: str,
) -> ManualEntitlementGrant:
    require_admin(actor)
    if not reason.strip():
        raise ValidationError({"reason": "required"})
    if expires_at is not None and expires_at <= starts_at:
        raise ValidationError({"expires_at": "must_follow_start"})
    with lock_capacity(account_id) as account:
        if plan.kind != account.kind:
            raise ValidationError({"plan": "account_kind_mismatch"})
        validate_capacity(account, seat_limit)
        grant = ManualEntitlementGrant.objects.filter(account=account).first()
        before = grant_snapshot(grant)
        if grant is None:
            grant = ManualEntitlementGrant(account=account)
        else:
            grant.revision += 1
        grant.plan = plan
        grant.seat_limit = seat_limit
        grant.starts_at = starts_at
        grant.expires_at = expires_at
        grant.revoked_at = None
        grant.reason = reason.strip()
        grant.save()
        audit(
            actor,
            "grant.updated",
            account.pk,
            {"before": before, "after": grant_snapshot(grant)},
        )
        return grant


def preview_grant(
    actor: Any,
    account_id: UUID,
    *,
    plan: Plan,
    seat_limit: int,
    starts_at: datetime,
    expires_at: datetime | None = None,
    reason: str,
) -> dict[str, Any]:
    """Validate a proposed grant while holding the same capacity lock as save."""
    require_admin(actor)
    if not reason.strip():
        raise ValidationError({"reason": "required"})
    if expires_at is not None and expires_at <= starts_at:
        raise ValidationError({"expires_at": "must_follow_start"})
    with lock_capacity(account_id) as account:
        if plan.kind != account.kind:
            raise ValidationError({"plan": "account_kind_mismatch"})
        validate_capacity(account, seat_limit)
    return {
        "plan": plan.pk,
        "seat_limit": seat_limit,
        "starts_at": starts_at.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "reason": reason.strip(),
    }


def revoke_grant(actor: Any, account_id: UUID, *, reason: str) -> None:
    require_admin(actor)
    if not reason.strip():
        raise ValidationError({"reason": "required"})
    with lock_capacity(account_id) as account:
        grant = ManualEntitlementGrant.objects.filter(account=account).first()
        if grant and grant.revoked_at is None:
            before = grant_snapshot(grant)
            grant.revoked_at = timezone.now()
            grant.revision += 1
            grant.save(update_fields=["revoked_at", "revision"])
            audit(
                actor,
                "grant.revoked",
                account.pk,
                {"reason": reason, "before": before, "after": grant_snapshot(grant)},
            )


def suspend_account(
    actor: Any, account_id: UUID, *, suspended: bool, reason: str
) -> None:
    require_admin(actor)
    if not reason.strip():
        raise ValidationError({"reason": "required"})
    with lock_capacity(account_id) as account:
        before = account.suspended
        account.suspended = suspended
        account.save(update_fields=["suspended"])
        audit(
            actor,
            "account.suspension_changed",
            account.pk,
            {"before": before, "after": suspended, "reason": reason},
        )
