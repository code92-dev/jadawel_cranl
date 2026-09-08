from typing import Any
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.api.checkout import VerifyInput
from jadawel_billing.api.views import BillingPagination
from jadawel_billing.models import BillingOrder, ProviderEvent, Subscription
from jadawel_billing.payments import reconcile_order


class AdminOrderSerializer(serializers.ModelSerializer[Any]):
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
    receipt = serializers.SerializerMethodField()

    def get_receipt(self, order: BillingOrder) -> dict[str, Any] | None:
        if order.status != "paid":
            return None
        subscription = Subscription.objects.filter(source_order=order).first()
        return {
            "order_id": str(order.pk),
            "amount": order.amount,
            "currency": order.currency,
            "paid_at": order.paid_at,
            "provider_payment_id": getattr(
                getattr(order, "payment_attempt", None), "provider_payment_id", None
            ),
            "period_end": subscription.period_end if subscription else None,
        }

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
        "account__responsible_user", "price", "payment_attempt"
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
