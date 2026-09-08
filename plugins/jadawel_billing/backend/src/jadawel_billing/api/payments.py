from typing import Any
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.api.receipts import ReceiptSerializer
from jadawel_billing.api.checkout import VerifyInput
from jadawel_billing.api.views import BillingPagination
from jadawel_billing.models import BillingOrder, BillingRefund, ProviderEvent
from jadawel_billing.payments import reconcile_order


class AdminOrderSerializer(ReceiptSerializer):
    given_id = serializers.UUIDField(source="payment_id", read_only=True)
    owner_email = serializers.EmailField(
        source="account.responsible_user.email", read_only=True
    )
    provider_payment_id = serializers.CharField(
        source="payment_attempt.provider_payment_id", read_only=True, allow_null=True
    )
    attempt_status = serializers.CharField(
        source="payment_attempt.status", read_only=True
    )
    failure_code = serializers.CharField(
        source="payment_attempt.failure_code", read_only=True
    )
    refund_status = serializers.SerializerMethodField()
    refunded_amount = serializers.SerializerMethodField()
    refundable_amount = serializers.SerializerMethodField()
    refund_attempts = serializers.IntegerField(
        source="refund.attempts", read_only=True, allow_null=True
    )
    refund_last_error = serializers.CharField(
        source="refund.last_error", read_only=True, allow_blank=True
    )

    def _refund(self, order: BillingOrder) -> BillingRefund | None:
        return getattr(order, "refund", None)

    def get_refund_status(self, order: BillingOrder) -> str | None:
        refund = self._refund(order)
        return refund.status if refund else None

    def get_refunded_amount(self, order: BillingOrder) -> int:
        refund = self._refund(order)
        return refund.amount if refund else 0

    def get_refundable_amount(self, order: BillingOrder) -> int:
        refund = self._refund(order)
        if refund and refund.status != BillingRefund.Status.SUCCEEDED:
            # An uncertain or failed provider attempt can be retried only with
            # the same amount as the recorded operation identity.
            return refund.amount
        return max(0, order.amount - (refund.amount if refund else 0))

    class Meta:
        model = BillingOrder
        fields = [
            "id",
            "account",
            "owner_email",
            "price",
            "payment_id",
            "given_id",
            "provider_payment_id",
            "attempt_status",
            "failure_code",
            "amount",
            "currency",
            "interval",
            "seats",
            "purpose",
            "refund_status",
            "refunded_amount",
            "refundable_amount",
            "refund_attempts",
            "refund_last_error",
            "mode",
            "status",
            "created_at",
            "paid_at",
            "receipt",
        ]


class AdminOrdersView(generics.ListAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderSerializer
    pagination_class = BillingPagination
    queryset = BillingOrder.objects.select_related(
        "account__responsible_user", "price", "payment_attempt", "refund"
    ).order_by("-created_at", "-id")


class ProviderEventSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = ProviderEvent
        fields = [
            "id",
            "event_id",
            "mode",
            "payment_id",
            "event_type",
            "status",
            "attempts",
            "error_code",
            "created_at",
        ]


class AdminProviderEventsView(generics.ListAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = ProviderEventSerializer
    pagination_class = BillingPagination
    queryset = ProviderEvent.objects.order_by("-created_at", "-id")


class AdminReconcileOrderView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request, order_id: UUID) -> Response:
        order = get_object_or_404(
            BillingOrder.objects.select_related("account", "price"), pk=order_id
        )
        data = VerifyInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            AdminOrderSerializer(
                reconcile_order(
                    request.user,
                    order,
                    data.validated_data.get("provider_payment_id"),
                )
            ).data
        )
