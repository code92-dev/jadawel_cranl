from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel_billing.models import BillingAccount, ManualEntitlementGrant, Subscription

_capacity_provider: Callable[[UUID], int] | None = None
_team_provisioner: Callable[[UUID], None] | None = None


def register_capacity_provider(provider: Callable[[UUID], int]) -> None:
    """Organizations registers its seat counter; Billing does not import it."""
    global _capacity_provider
    if _capacity_provider is not None and _capacity_provider is not provider:
        raise RuntimeError("A billing capacity provider is already registered")
    _capacity_provider = provider


def register_team_provisioner(provisioner: Callable[[UUID], None]) -> None:
    """Organizations registers paid-Team provisioning without a billing import."""
    global _team_provisioner
    if _team_provisioner is not None and _team_provisioner is not provisioner:
        raise RuntimeError("A billing team provisioner is already registered")
    _team_provisioner = provisioner


def provision_team(account_id: UUID) -> None:
    if _team_provisioner is None:
        return
    _team_provisioner(account_id)


def has_team_provisioner() -> bool:
    return _team_provisioner is not None


def occupied_seats(account: BillingAccount) -> int:
    if account.kind == BillingAccount.Kind.INDIVIDUAL:
        return 1
    return _capacity_provider(account.pk) if _capacity_provider else 0


@contextmanager
def lock_capacity(account_id: UUID) -> Iterator[BillingAccount]:
    """Shared lock for entitlement changes and membership acceptance."""
    with transaction.atomic():
        yield BillingAccount.objects.select_for_update().get(pk=account_id)


def validate_capacity(account: BillingAccount, seats: int) -> None:
    if seats < max(1, occupied_seats(account)):
        raise ValidationError({"seat_limit": "below_usage"})
    if account.kind == BillingAccount.Kind.INDIVIDUAL and seats != 1:
        raise ValidationError({"seat_limit": "individual_requires_one_seat"})


def get_effective_entitlements(
    account_id: UUID,
    at: datetime | None = None,
    *,
    proposed_grant: ManualEntitlementGrant | None = None,
) -> dict[str, Any]:
    at = at or timezone.now()
    account = BillingAccount.objects.get(pk=account_id)
    result: dict[str, Any] = {
        "source": "restricted",
        "plan": None,
        "seat_limit": 0,
        "capabilities": [],
        "valid_until": None,
        "revision": 0,
        "restriction_reason": "unprovisioned",
    }
    if account.suspended:
        return {
            **result,
            "source": "suspended",
            "restriction_reason": "admin_suspension",
        }
    grant = (
        proposed_grant
        or ManualEntitlementGrant.objects.filter(
            account=account, revoked_at__isnull=True
        ).first()
    )
    if (
        grant
        and grant.starts_at <= at
        and (grant.expires_at is None or at < grant.expires_at)
    ):
        return {
            "source": "manual",
            "plan": grant.plan_id,
            "seat_limit": grant.seat_limit,
            "capabilities": ["data_write"]
            + (["organization"] if account.kind == "TEAM" else []),
            "valid_until": grant.expires_at,
            "revision": grant.revision,
            "restriction_reason": None,
        }
    subscription = Subscription.objects.filter(account=account).first()
    if subscription and subscription.period_start <= at < subscription.period_end:
        return {
            **result,
            "source": "paid",
            "plan": subscription.price.plan_id,
            "seat_limit": subscription.seats,
            "capabilities": ["data_write"]
            + (["organization"] if account.kind == "TEAM" else []),
            "valid_until": subscription.period_end,
            "restriction_reason": None,
        }
    grace_days = max(0, int(getattr(settings, "JADAWEL_BILLING_GRACE_DAYS", 7)))
    if (
        subscription
        and subscription.status
        in {Subscription.Status.GRACE, Subscription.Status.PAST_DUE}
        and subscription.period_end
        <= at
        < subscription.period_end + timedelta(days=grace_days)
    ):
        return {
            "source": "grace",
            "plan": subscription.price.plan_id,
            "seat_limit": subscription.seats,
            "capabilities": ["data_write"]
            + (["organization"] if account.kind == "TEAM" else []),
            "valid_until": subscription.period_end + timedelta(days=grace_days),
            "revision": 0,
            "restriction_reason": "renewal_grace",
        }
    return result


def require_entitlement(account_id: UUID, capability: str) -> dict[str, Any]:
    result = get_effective_entitlements(account_id)
    if capability not in result["capabilities"]:
        raise PermissionDenied("entitlement_required")
    return result
