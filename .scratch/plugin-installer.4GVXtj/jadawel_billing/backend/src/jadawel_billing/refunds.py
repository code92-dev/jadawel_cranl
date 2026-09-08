from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .errors import ProviderUnavailable
from .handlers import audit, require_admin
from .models import BillingAccount, BillingOrder, BillingRefund, ExternalPayment
from .payments import billing_mode
from .providers.moyasar import MoyasarClient


def refund_order(
    actor: Any, order: BillingOrder, *, amount: int | None = None, reason: str
) -> BillingRefund:
    require_admin(actor)
    if not reason.strip():
        raise ValidationError({"reason": "required"})
    requested_amount = amount or order.amount
    if (
        order.status != "paid"
        or requested_amount < 1
        or requested_amount > order.amount
    ):
        raise ValidationError({"amount": "invalid_refund_amount"})
    with transaction.atomic():
        refund, created = BillingRefund.objects.get_or_create(
            order=order,
            defaults={
                "amount": requested_amount,
                "currency": order.currency,
                "reason": reason.strip(),
                "actor": actor,
            },
        )
        if not created:
            if refund.status == BillingRefund.Status.SUCCEEDED:
                return refund
            if refund.status == BillingRefund.Status.PROCESSING:
                if refund.updated_at > timezone.now() - timedelta(minutes=5):
                    raise ValidationError({"refund": "already_processing"})
                # A worker may have exited after the state transition and
                # before the provider response. Re-enter the reconciliation
                # path after the short processing lease expires.
                refund.status = BillingRefund.Status.PENDING
                refund.save(update_fields=["status", "updated_at"])
            if refund.amount != requested_amount:
                raise ValidationError({"amount": "must_match_previous_attempt"})
        amount = refund.amount
    provider_id = getattr(order.payment_attempt, "provider_payment_id", None)
    if not provider_id:
        raise ValidationError({"payment": "provider_id_required"})

    # Moyasar documents refund recovery as a payment status fetch followed by
    # one retry only when the original payment is still refundable. Do this
    # outside the database transaction so provider I/O never holds a DB lock.
    if not created and refund.attempts:
        try:
            payment = MoyasarClient(
                secret_key=settings.JADAWEL_MOYASAR_SECRET_KEY, mode=billing_mode()
            ).fetch(provider_id)
        except ProviderUnavailable as exc:
            raise ValidationError({"refund": "reconciliation_unavailable"}) from exc
        provider_status = payment.get("status")
        if provider_status == "refunded":
            with transaction.atomic():
                refund = BillingRefund.objects.select_for_update().get(pk=refund.pk)
                refund.status = BillingRefund.Status.SUCCEEDED
                refund.last_error = ""
                refund.updated_at = timezone.now()
                refund.save(update_fields=["status", "last_error", "updated_at"])
                audit(
                    actor,
                    "payment.refund_reconciled",
                    order.account_id,
                    {"order": str(order.pk), "amount": refund.amount},
                )
                return refund
        if provider_status not in {"paid", "captured"}:
            with transaction.atomic():
                refund = BillingRefund.objects.select_for_update().get(pk=refund.pk)
                refund.status = BillingRefund.Status.FAILED
                refund.last_error = f"payment_status:{provider_status or 'unknown'}"[
                    :120
                ]
                refund.updated_at = timezone.now()
                refund.save(update_fields=["status", "last_error", "updated_at"])
            raise ValidationError({"refund": "payment_not_refundable"})

    with transaction.atomic():
        refund = BillingRefund.objects.select_for_update().get(pk=refund.pk)
        if refund.status == BillingRefund.Status.SUCCEEDED:
            return refund
        if refund.status == BillingRefund.Status.PROCESSING:
            raise ValidationError({"refund": "already_processing"})
        if refund.attempts >= 2:
            raise ValidationError({"refund": "retry_limit_reached"})
        refund.status = BillingRefund.Status.PROCESSING
        refund.attempts += 1
        refund.last_error = ""
        refund.save(update_fields=["status", "attempts", "last_error", "updated_at"])
        amount = refund.amount
    try:
        payload = MoyasarClient(
            secret_key=settings.JADAWEL_MOYASAR_SECRET_KEY, mode=billing_mode()
        ).refund(provider_id, amount)
        status = payload.get("status", "succeeded")
        with transaction.atomic():
            refund.status = (
                BillingRefund.Status.SUCCEEDED
                if status in {"refunded", "succeeded", "paid"}
                else BillingRefund.Status.FAILED
            )
            refund.last_error = (
                ""
                if refund.status == BillingRefund.Status.SUCCEEDED
                else str(
                    payload.get("message") or payload.get("error") or "provider_failed"
                )[:120]
            )
            refund.provider_refund_id = (
                str(payload.get("id"))
                if payload.get("id")
                else refund.provider_refund_id
            )
            refund.updated_at = timezone.now()
            refund.save(
                update_fields=[
                    "status",
                    "provider_refund_id",
                    "last_error",
                    "updated_at",
                ]
            )
            audit(
                actor,
                "payment.refunded",
                order.account_id,
                {"order": str(order.pk), "amount": amount},
            )
            return refund
    except ProviderUnavailable as exc:
        BillingRefund.objects.filter(pk=refund.pk).update(
            status=BillingRefund.Status.PENDING,
            last_error="provider_unavailable",
            updated_at=timezone.now(),
        )
        raise exc


@transaction.atomic
def record_external_payment(
    actor: Any,
    account: BillingAccount,
    *,
    amount: int,
    reference: str,
    paid_at: datetime,
    notes: str = "",
) -> ExternalPayment:
    require_admin(actor)
    if amount < 1 or not reference.strip():
        raise ValidationError({"payment": "invalid"})
    payment, created = ExternalPayment.objects.get_or_create(
        reference=reference.strip(),
        defaults={
            "account": account,
            "amount": amount,
            "currency": "SAR",
            "paid_at": paid_at,
            "notes": notes.strip(),
            "actor": actor,
        },
    )
    if not created:
        if payment.account_id != account.pk:
            raise ValidationError({"reference": "already_used"})
        if (
            payment.amount != amount
            or payment.paid_at != paid_at
            or payment.notes != notes.strip()
        ):
            raise ValidationError({"reference": "already_used_with_different_details"})
        return payment
    audit(
        actor,
        "payment.external_recorded",
        account.pk,
        {"reference": payment.reference, "amount": payment.amount},
    )
    return payment
