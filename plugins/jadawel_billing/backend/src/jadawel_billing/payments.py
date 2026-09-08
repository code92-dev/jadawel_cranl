from calendar import monthrange
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel_billing.errors import ProviderUnavailable
from jadawel_billing.entitlements import has_team_provisioner, provision_team
from jadawel_billing.handlers import audit, require_admin
from jadawel_billing.models import (
    BillingAccount,
    BillingOrder,
    PaymentAttempt,
    PlanPrice,
    Subscription,
)
from jadawel_billing.providers.moyasar import MoyasarClient


def billing_mode() -> str:
    mode = getattr(settings, "JADAWEL_BILLING_MODE", "test")
    if mode not in ("test", "live"):
        raise ProviderUnavailable()
    if mode == "live" and not getattr(settings, "JADAWEL_BILLING_LIVE_ENABLED", False):
        raise ProviderUnavailable()
    return mode


def require_payer(actor: Any, account: BillingAccount) -> None:
    if (
        not actor.is_authenticated
        or not actor.is_active
        or account.responsible_user_id != actor.pk
    ):
        raise PermissionDenied()


def create_order(
    actor: Any, account: BillingAccount, price: PlanPrice, seats: int
) -> BillingOrder:
    require_payer(actor, account)
    mode = billing_mode()
    if account.kind == "INDIVIDUAL" and seats != 1:
        raise ValidationError({"account": "individual_requires_one_seat"})
    if account.kind == "TEAM" and not has_team_provisioner():
        raise ValidationError({"account": "organizations_required"})
    if (
        not price.available
        or not price.plan.available
        or price.plan.kind != account.kind
        or price.amount < 1
    ):
        raise ValidationError({"price": "unavailable"})
    with transaction.atomic():
        account = BillingAccount.objects.select_for_update().get(pk=account.pk)
        require_payer(actor, account)
        if account.suspended:
            raise PermissionDenied("account_suspended")
        subscription = Subscription.objects.filter(
            account=account, period_end__gt=timezone.now()
        ).first()
        if subscription:
            raise ValidationError({"account": "subscription_already_active"})
        pending = BillingOrder.objects.filter(account=account, status="pending").first()
        if pending:
            if pending.price_id != price.pk or pending.mode != mode:
                raise ValidationError({"account": "resolve_pending_order"})
            return pending
        order = BillingOrder.objects.create(
            account=account,
            price=price,
            seats=seats,
            amount=price.amount * seats
            if account.kind == BillingAccount.Kind.TEAM
            else price.amount,
            currency=price.currency,
            interval=price.interval,
            mode=mode,
        )
        PaymentAttempt.objects.create(
            order=order, given_id=order.payment_id, provider_mode=mode
        )
        return order


def fetch_payment(
    order: BillingOrder, provider_payment_id: str | None = None
) -> dict[str, Any]:
    if order.mode != billing_mode():
        raise ProviderUnavailable()
    secret = getattr(settings, "JADAWEL_MOYASAR_SECRET_KEY", "")
    provider_payment_id = provider_payment_id or getattr(
        order.payment_attempt, "provider_payment_id", None
    )
    if not provider_payment_id:
        raise ValidationError({"payment": "provider_id_required"})
    return MoyasarClient(secret_key=secret, mode=order.mode).fetch(provider_payment_id)


def period_end(start: datetime, interval: str) -> datetime:
    month = start.month + (12 if interval == "YEAR" else 1)
    year = start.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return start.replace(
        year=year, month=month, day=min(start.day, monthrange(year, month)[1])
    )


def _verify_order(
    actor: Any,
    order: BillingOrder,
    *,
    payer_required: bool,
    system: bool = False,
    provider_payment_id: str | None = None,
) -> BillingOrder:
    if payer_required:
        require_payer(actor, order.account)
    elif not system:
        require_admin(actor)
    bound_provider_payment_id: str | None = None
    with transaction.atomic():
        attempt = PaymentAttempt.objects.select_for_update().get(order=order)
        if attempt.provider_mode != order.mode:
            raise ValidationError({"payment_id": "environment_mismatch"})
        if provider_payment_id is not None:
            candidate = provider_payment_id.strip()
            if not candidate or len(candidate) > 100:
                raise ValidationError({"payment_id": "invalid"})
            reused = (
                PaymentAttempt.objects.filter(provider_payment_id=candidate)
                .filter(provider_mode=order.mode)
                .exclude(pk=attempt.pk)
                .exists()
            )
            if reused:
                raise ValidationError({"payment_id": "already_used"})
            if attempt.provider_payment_id not in (None, candidate):
                raise ValidationError({"payment_id": "already_bound"})
            bound_provider_payment_id = candidate
        else:
            bound_provider_payment_id = attempt.provider_payment_id
        if not bound_provider_payment_id:
            raise ValidationError({"payment_id": "provider_id_required"})
    payment = fetch_payment(order, bound_provider_payment_id)
    metadata = payment.get("metadata")
    if (
        payment.get("id") != bound_provider_payment_id
        or type(payment.get("amount")) is not int
        or payment["amount"] != order.amount
        or payment.get("currency") != order.currency
        or not isinstance(metadata, dict)
        or metadata.get("billing_order") != str(order.pk)
    ):
        raise ValidationError({"payment": "order_mismatch"})
    with transaction.atomic():
        account = BillingAccount.objects.select_for_update().get(pk=order.account_id)
        if payer_required:
            require_payer(actor, account)
        order = BillingOrder.objects.select_for_update().get(pk=order.pk)
        attempt = PaymentAttempt.objects.select_for_update().get(order=order)
        if attempt.provider_payment_id not in (None, bound_provider_payment_id):
            raise ValidationError({"payment_id": "already_bound"})
        if attempt.provider_payment_id is None:
            attempt.provider_mode = order.mode
            attempt.provider_payment_id = bound_provider_payment_id
            try:
                attempt.save(
                    update_fields=["provider_mode", "provider_payment_id", "updated_at"]
                )
            except IntegrityError as exc:
                raise ValidationError({"payment_id": "already_used"}) from exc
        provider_status = payment.get("status")
        if order.status == "paid":
            if provider_status in {
                "failed",
                "refunded",
                "voided",
                "canceled",
                "cancelled",
            }:
                raise ValidationError(
                    {"payment": "settlement_reversal_requires_review"}
                )
            return order
        if provider_status in {"failed", "canceled", "cancelled", "expired"}:
            attempt.status = PaymentAttempt.Status.FAILED
            attempt.failure_code = str(
                payment.get("failure_code")
                or payment.get("failure_message")
                or "failed"
            )[:80]
            attempt.verified_at = timezone.now()
            attempt.save(
                update_fields=["status", "failure_code", "verified_at", "updated_at"]
            )
            order.status = "failed"
            order.save(update_fields=["status"])
            return order
        if provider_status not in {"paid", "captured"}:
            # Uncertain results keep the original ID; no automatic second charge.
            attempt.status = (
                provider_status
                if provider_status in PaymentAttempt.Status.values
                else PaymentAttempt.Status.PENDING
            )
            attempt.save(update_fields=["status", "updated_at"])
            return order
        now = timezone.now()
        Subscription.objects.update_or_create(
            account=account,
            defaults={
                "price": order.price,
                "seats": order.seats,
                "period_start": now,
                "period_end": period_end(now, order.interval),
                "source_order": order,
                "cancel_at_period_end": False,
            },
        )
        order.status = "paid"
        order.paid_at = now
        order.save(update_fields=["status", "paid_at"])
        attempt.status = PaymentAttempt.Status.PAID
        attempt.verified_at = now
        attempt.save(update_fields=["status", "verified_at", "updated_at"])
        audit(
            None if system else actor,
            "payment.verified",
            account.pk,
            {
                "order": str(order.pk),
                "amount": order.amount,
                "currency": order.currency,
            },
        )
        if account.kind == BillingAccount.Kind.TEAM:
            provision_team(account.pk)
        return order


def verify_order(
    actor: Any, order: BillingOrder, provider_payment_id: str | None = None
) -> BillingOrder:
    """Verify a payer-requested order after the browser flow returns."""
    return _verify_order(
        actor, order, payer_required=True, provider_payment_id=provider_payment_id
    )


def reconcile_order(
    actor: Any, order: BillingOrder, provider_payment_id: str | None = None
) -> BillingOrder:
    """Verify an order from an audited staff reconciliation action."""
    return _verify_order(
        actor, order, payer_required=False, provider_payment_id=provider_payment_id
    )


def reconcile_order_system(
    order: BillingOrder, provider_payment_id: str | None = None
) -> BillingOrder:
    """Verify an order from the durable Celery reconciler."""
    return _verify_order(
        actor=None,
        order=order,
        payer_required=False,
        system=True,
        provider_payment_id=provider_payment_id,
    )
