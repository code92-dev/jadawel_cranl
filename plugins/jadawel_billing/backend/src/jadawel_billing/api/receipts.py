from typing import Any

from rest_framework import serializers

from jadawel_billing.models import BillingOrder
from jadawel_billing.payments import period_end


class PaymentAttemptFieldsMixin(serializers.Serializer[Any]):
    """Order fields that identify and report on its payment attempt.

    DRF only collects declared fields from Serializer bases, so this stays a
    Serializer. Subclasses list the fields in their own Meta.fields.
    """

    given_id = serializers.UUIDField(source="payment_id", read_only=True)
    provider_payment_id = serializers.CharField(
        source="payment_attempt.provider_payment_id", read_only=True, allow_null=True
    )
    attempt_status = serializers.CharField(
        source="payment_attempt.status", read_only=True
    )
    failure_code = serializers.CharField(
        source="payment_attempt.failure_code", read_only=True
    )


class ReceiptSerializer(serializers.ModelSerializer[Any]):
    receipt = serializers.SerializerMethodField()

    def get_receipt(self, order: BillingOrder) -> dict[str, Any] | None:
        if order.status != "paid":
            return None
        end = period_end(order.paid_at or order.created_at, order.interval)
        return {
            "order_id": str(order.pk),
            "amount": order.amount,
            "currency": order.currency,
            "paid_at": order.paid_at,
            "provider_payment_id": getattr(
                getattr(order, "payment_attempt", None), "provider_payment_id", None
            ),
            "period_end": end,
        }
