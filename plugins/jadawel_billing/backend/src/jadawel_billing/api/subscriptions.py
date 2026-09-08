from typing import Any
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.models import (
    BillingAccount,
    PaymentMethod,
    PlanPrice,
    Subscription,
)
from jadawel_billing.payment_methods import (
    list_payment_methods,
    revoke_payment_method,
    save_payment_method,
)
from jadawel_billing.refunds import record_external_payment, refund_order
from jadawel_billing.subscriptions import schedule_subscription_change, set_cancellation


class PaymentMethodInput(serializers.Serializer[Any]):
    provider_token = serializers.CharField(max_length=160)
    provider_payment_id = serializers.CharField(max_length=100)
    consent = serializers.BooleanField()
    brand = serializers.CharField(max_length=40, required=False, default="")
    last4 = serializers.CharField(max_length=4, required=False, default="")
    exp_month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    exp_year = serializers.IntegerField(required=False, min_value=2020, max_value=3000)


class PaymentMethodSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "brand",
            "last4",
            "exp_month",
            "exp_year",
            "consent_at",
            "created_at",
        ]


class PaymentMethodsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_account(self, request: Request, account_id: UUID) -> BillingAccount:
        return get_object_or_404(
            BillingAccount, pk=account_id, responsible_user_id=request.user.pk
        )

    def get(self, request: Request, account_id: UUID) -> Response:
        account = self.get_account(request, account_id)
        return Response(
            PaymentMethodSerializer(
                list_payment_methods(request.user, account), many=True
            ).data
        )

    def post(self, request: Request, account_id: UUID) -> Response:
        account = self.get_account(request, account_id)
        data = PaymentMethodInput(data=request.data)
        data.is_valid(raise_exception=True)
        method = save_payment_method(request.user, account, **data.validated_data)
        return Response(PaymentMethodSerializer(method).data, status=201)


class PaymentMethodDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, account_id: UUID, method_id: int) -> Response:
        account = get_object_or_404(
            BillingAccount, pk=account_id, responsible_user_id=request.user.pk
        )
        method = get_object_or_404(PaymentMethod, pk=method_id, account=account)
        revoke_payment_method(request.user, method)
        return Response(status=204)


class CancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, account_id: UUID) -> Response:
        account = get_object_or_404(BillingAccount, pk=account_id)
        subscription = get_object_or_404(Subscription, account=account)
        subscription = set_cancellation(
            request.user, subscription, bool(request.data.get("cancel", True))
        )
        return Response({"cancel_at_period_end": subscription.cancel_at_period_end})


class SubscriptionChangeInput(serializers.Serializer[Any]):
    price = serializers.PrimaryKeyRelatedField(queryset=PlanPrice.objects.all())
    seats = serializers.IntegerField(min_value=1, max_value=100000)


class SubscriptionChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, account_id: UUID) -> Response:
        account = get_object_or_404(BillingAccount, pk=account_id)
        subscription = get_object_or_404(Subscription, account=account)
        data = SubscriptionChangeInput(data=request.data)
        data.is_valid(raise_exception=True)
        change = schedule_subscription_change(
            request.user, subscription, **data.validated_data
        )
        return Response(
            {
                "price": change.price_id,
                "seats": change.seats,
                "effective_at": change.effective_at,
            }
        )


class RefundInput(serializers.Serializer[Any]):
    amount = serializers.IntegerField(required=False, min_value=1)
    reason = serializers.CharField(max_length=500)


class AdminRefundView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request, order_id: UUID) -> Response:
        from jadawel_billing.models import BillingOrder

        order = get_object_or_404(BillingOrder, pk=order_id)
        data = RefundInput(data=request.data)
        data.is_valid(raise_exception=True)
        refund = refund_order(request.user, order, **data.validated_data)
        return Response(
            {"id": refund.pk, "status": refund.status, "amount": refund.amount}
        )


class ExternalPaymentInput(serializers.Serializer[Any]):
    account = serializers.PrimaryKeyRelatedField(queryset=BillingAccount.objects.all())
    amount = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(max_length=120)
    paid_at = serializers.DateTimeField()
    notes = serializers.CharField(max_length=500, required=False, default="")


class AdminExternalPaymentView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request) -> Response:
        data = ExternalPaymentInput(data=request.data)
        data.is_valid(raise_exception=True)
        payment = record_external_payment(request.user, **data.validated_data)
        return Response(
            {
                "id": payment.pk,
                "reference": payment.reference,
                "amount": payment.amount,
            },
            status=201,
        )
