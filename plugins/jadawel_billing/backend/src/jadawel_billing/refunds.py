from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

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
            if refund.status == BillingRefund.Status.PENDING:
                raise ValidationError({"refund": "already_processing"})
            if refund.amount != requested_amount:
                raise ValidationError({"amount": "must_match_previous_attempt"})
        amount = refund.amount
    provider_id = getattr(order.payment_attempt, "provider_payment_id", None)
    if not provider_id:
        raise ValidationError({"payment": "provider_id_required"})
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
            refund.provider_refund_id = (
                str(payload.get("id"))
                if payload.get("id")
                else refund.provider_refund_id
            )
            refund.updated_at = timezone.now()
            refund.save(update_fields=["status", "provider_refund_id", "updated_at"])
            audit(
                actor,
                "payment.refunded",
                order.account_id,
                {"order": str(order.pk), "amount": amount},
            )
            return refund
    except Exception:
        BillingRefund.objects.filter(pk=refund.pk).update(
            status=BillingRefund.Status.PENDING
        )
        raise


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
    if not created and payment.account_id != account.pk:
        raise ValidationError({"reference": "already_used"})
    audit(
        actor,
        "payment.external_recorded",
        account.pk,
        {"reference": payment.reference, "amount": payment.amount},
    )
    return payment
