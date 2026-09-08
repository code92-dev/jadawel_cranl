from typing import Any
from calendar import monthrange

from rest_framework import serializers

from jadawel_billing.models import BillingOrder


class ReceiptSerializer(serializers.ModelSerializer[Any]):
    receipt = serializers.SerializerMethodField()

    def get_receipt(self, order: BillingOrder) -> dict[str, Any] | None:
        if order.status != "paid":
            return None
        start = order.paid_at or order.created_at
        month = start.month + (12 if order.interval == "YEAR" else 1)
        year = start.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        period_end = start.replace(
            year=year, month=month, day=min(start.day, monthrange(year, month)[1])
        )
        return {
            "order_id": str(order.pk),
            "amount": order.amount,
            "currency": order.currency,
            "paid_at": order.paid_at,
            "provider_payment_id": getattr(
                getattr(order, "payment_attempt", None), "provider_payment_id", None
            ),
            "period_end": period_end if start else None,
        }
