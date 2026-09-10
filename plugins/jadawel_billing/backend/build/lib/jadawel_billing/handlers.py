from typing import Any

from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel_billing.models import BillingAccount, BillingAuditEvent, Plan, PlanPrice


def require_admin(actor: Any) -> None:
    if not actor.is_authenticated or not actor.is_active or not actor.is_staff:
        raise PermissionDenied()


def create_account(actor: Any, *, kind: str, responsible_user: Any) -> BillingAccount:
    require_admin(actor)
    if kind not in BillingAccount.Kind.values:
        raise ValidationError({"kind": "invalid"})
    try:
        with transaction.atomic():
            account = BillingAccount.objects.create(
                kind=kind, responsible_user=responsible_user
            )
            audit(actor, "account.created", account.pk, {"kind": kind})
            return account
    except IntegrityError as exc:
        raise ValidationError({"responsible_user": "account_exists"}) from exc


def audit(actor: Any, action: str, target: Any, details: dict[str, Any]) -> None:
    BillingAuditEvent.objects.create(
        actor=actor, action=action, target=str(target), details=details
    )


@transaction.atomic
def create_plan(actor: Any, **data: Any) -> Plan:
    require_admin(actor)
    plan = Plan(**data)
    plan.full_clean()
    plan.save()
    audit(actor, "plan.created", plan.pk, data)
    return plan


@transaction.atomic
def create_price(actor: Any, *, plan: Plan, **data: Any) -> PlanPrice:
    require_admin(actor)
    price = PlanPrice(plan=plan, **data)
    price.full_clean()
    price.save()
    audit(actor, "price.created", price.pk, {**data, "plan": plan.pk})
    return price


@transaction.atomic
def set_availability(actor: Any, instance: Any, available: bool) -> Plan | PlanPrice:
    require_admin(actor)
    instance = type(instance).objects.select_for_update().get(pk=instance.pk)
    previous = instance.available
    instance.available = available
    instance.save(update_fields=["available"])
    audit(
        actor,
        "availability.updated",
        instance.pk,
        {
            "type": type(instance).__name__,
            "before": previous,
            "after": available,
        },
    )
    return instance
