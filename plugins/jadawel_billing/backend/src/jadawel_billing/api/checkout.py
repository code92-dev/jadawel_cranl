from typing import Any
from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.api.receipts import ReceiptSerializer
from jadawel_billing.errors import ProviderUnavailable
from jadawel_billing.entitlements import get_effective_entitlements
from jadawel_billing.models import BillingAccount, BillingOrder, PlanPrice, Subscription
from jadawel_billing.payments import (
    billing_mode,
    create_order,
    require_payer,
    verify_order,
)


class OrderInput(serializers.Serializer[Any]):
    account = serializers.PrimaryKeyRelatedField(queryset=BillingAccount.objects.all())
    price = serializers.PrimaryKeyRelatedField(
        queryset=PlanPrice.objects.select_related("plan")
    )
    seats = serializers.IntegerField(min_value=1, max_value=100000)


class OrderSerializer(ReceiptSerializer):
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

    class Meta:
        model = BillingOrder
        fields = [
            "id",
            "payment_id",
            "given_id",
            "provider_payment_id",
            "attempt_status",
            "failure_code",
            "amount",
            "currency",
            "status",
            "seats",
            "created_at",
            "paid_at",
            "receipt",
        ]


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        orders = (
            BillingOrder.objects.select_related("payment_attempt")
            .filter(account__responsible_user_id=request.user.pk)
            .order_by("-created_at")[:50]
        )
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request: Request) -> Response:
        data = OrderInput(data=request.data)
        data.is_valid(raise_exception=True)
        order = create_order(request.user, **data.validated_data)
        return Response(OrderSerializer(order).data, status=201)


class VerifyInput(serializers.Serializer[Any]):
    provider_payment_id = serializers.CharField(
        required=False, allow_blank=False, max_length=100
    )


class VerifyOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, order_id: UUID) -> Response:
        order = get_object_or_404(
            BillingOrder.objects.select_related("account", "price", "payment_attempt"),
            pk=order_id,
            account__responsible_user_id=request.user.pk,
        )
        data = VerifyInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            OrderSerializer(
                verify_order(
                    request.user,
                    order,
                    data.validated_data.get("provider_payment_id"),
                )
            ).data
        )


class AccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, account_id: UUID) -> Response:
        account = get_object_or_404(
            BillingAccount, pk=account_id, responsible_user_id=request.user.pk
        )
        require_payer(request.user, account)
        subscription = Subscription.objects.filter(account=account).first()
        return Response(
            {
                "id": str(account.pk),
                "effective": get_effective_entitlements(account.pk),
                "subscription": None
                if subscription is None
                else {
                    "price": subscription.price_id,
                    "status": subscription.status,
                    "period_start": subscription.period_start,
                    "seats": subscription.seats,
                    "period_end": subscription.period_end,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                },
            }
        )


class CheckoutOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        mode = billing_mode()
        key = getattr(settings, "JADAWEL_MOYASAR_PUBLISHABLE_KEY", "")
        if not key.startswith(f"pk_{mode}_"):
            raise ProviderUnavailable()
        accounts = BillingAccount.objects.filter(responsible_user_id=request.user.pk)
        prices = PlanPrice.objects.filter(
            available=True, plan__available=True, amount__gt=0
        ).select_related("plan")
        return Response(
            {
                "publishable_key": key,
                "mode": mode,
                "accounts": [{"id": str(a.pk), "kind": a.kind} for a in accounts],
                "prices": [
                    {
                        "id": p.pk,
                        "name": p.plan.name,
                        "kind": p.plan.kind,
                        "amount": p.amount,
                        "currency": p.currency,
                        "interval": p.interval,
                    }
                    for p in prices
                ],
            }
        )
