from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .entitlements import get_effective_entitlements, validate_capacity
from .models import (
    BillingAccount,
    BillingOrder,
    PaymentAttempt,
    PaymentMethod,
    PlanPrice,
    Subscription,
    SubscriptionChange,
)
from .payments import billing_mode
from .providers.moyasar import MoyasarClient


@transaction.atomic
def set_cancellation(
    actor: Any, subscription: Subscription, cancel: bool
) -> Subscription:
    if not actor.is_staff and subscription.account.responsible_user_id != actor.pk:
        raise ValidationError({"subscription": "not_owner"})
    subscription.cancel_at_period_end = cancel
    subscription.save(update_fields=["cancel_at_period_end"])
    return subscription


@transaction.atomic
def schedule_subscription_change(
    actor: Any, subscription: Subscription, *, price: PlanPrice, seats: int
) -> SubscriptionChange:
    if not actor.is_staff and subscription.account.responsible_user_id != actor.pk:
        raise ValidationError({"subscription": "not_owner"})
    if price.plan.kind != subscription.account.kind:
        raise ValidationError({"price": "account_kind_mismatch"})
    if seats > subscription.seats:
        raise ValidationError({"seats": "seat_increase_requires_verified_payment"})
    with transaction.atomic():
        account = BillingAccount.objects.select_for_update().get(
            pk=subscription.account_id
        )
        validate_capacity(account, seats)
    return SubscriptionChange.objects.update_or_create(
        subscription=subscription,
        defaults={
            "price": price,
            "seats": seats,
            "effective_at": subscription.period_end,
        },
    )[0]


def renew_due_subscriptions() -> int:
    """Charge each due subscription once, retaining the original operation ID."""
    mode = billing_mode()
    renewed = 0
    now = timezone.now()
    for subscription in (
        Subscription.objects.select_related("account", "price")
        .filter(
            period_end__lte=now,
            cancel_at_period_end=False,
            status__in=[
                Subscription.Status.ACTIVE,
                Subscription.Status.GRACE,
                Subscription.Status.PAST_DUE,
            ],
        )
        .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=now))[:100]
    ):
        with transaction.atomic():
            account = BillingAccount.objects.select_for_update().get(
                pk=subscription.account_id
            )
            if get_effective_entitlements(account.pk).get("source") == "manual":
                continue
            method = PaymentMethod.objects.filter(
                account=account, revoked_at__isnull=True
            ).first()
            if method is None:
                subscription.status = Subscription.Status.GRACE
                subscription.retry_count += 1
                subscription.next_retry_at = now + timedelta(days=1)
                subscription.save(
                    update_fields=["status", "retry_count", "next_retry_at"]
                )
                continue
            scheduled = (
                SubscriptionChange.objects.filter(
                    subscription=subscription, effective_at__lte=now
                )
                .select_related("price")
                .first()
            )
            price = scheduled.price if scheduled else subscription.price
            seats = scheduled.seats if scheduled else subscription.seats
            if scheduled:
                try:
                    validate_capacity(account, seats)
                except ValidationError:
                    subscription.status = Subscription.Status.GRACE
                    subscription.retry_count += 1
                    subscription.next_retry_at = now + timedelta(days=1)
                    subscription.save(
                        update_fields=["status", "retry_count", "next_retry_at"]
                    )
                    continue
            amount = (
                price.amount * seats
                if account.kind == BillingAccount.Kind.TEAM
                else price.amount
            )
            order, _ = BillingOrder.objects.get_or_create(
                account=account,
                status="pending",
                defaults={
                    "price": price,
                    "seats": seats,
                    "amount": amount,
                    "currency": price.currency,
                    "interval": price.interval,
                    "mode": mode,
                },
            )
            PaymentAttempt.objects.get_or_create(
                order=order,
                defaults={"given_id": order.payment_id, "provider_mode": mode},
            )
        try:
            payment = MoyasarClient(
                secret_key=settings.JADAWEL_MOYASAR_SECRET_KEY,
                mode=mode,
            ).charge(
                amount=order.amount,
                currency=order.currency,
                token=method.provider_token,
                given_id=order.payment_id,
                metadata={"billing_order": str(order.pk)},
            )
            provider_id = payment.get("id")
            if not provider_id:
                raise ValidationError({"payment": "provider_id_missing"})
            from .payments import reconcile_order_system

            reconciled = reconcile_order_system(order, provider_payment_id=provider_id)
            if reconciled.status == "paid":
                SubscriptionChange.objects.filter(
                    subscription_id=subscription.pk,
                    effective_at__lte=timezone.now(),
                ).delete()
            renewed += 1
        except Exception:
            subscription.status = Subscription.Status.GRACE
            subscription.retry_count += 1
            subscription.next_retry_at = now + timedelta(
                days=1 if subscription.retry_count == 1 else 3
            )
            subscription.save(update_fields=["status", "retry_count", "next_retry_at"])
    return renewed
