from typing import Any
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.api.views import BillingPagination
from jadawel_billing.entitlements import get_effective_entitlements
from jadawel_billing.grants import (
    grant_snapshot,
    preview_grant,
    replace_grant,
    revoke_grant,
    suspend_account,
)
from jadawel_billing.models import (
    BillingAccount,
    BillingAuditEvent,
    ManualEntitlementGrant,
    Plan,
    Subscription,
)


class GrantSerializer(serializers.Serializer[Any]):
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all())
    seat_limit = serializers.IntegerField(min_value=1, max_value=100000)
    starts_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(
        required=False, allow_null=True, default=None
    )
    reason = serializers.CharField(max_length=500, allow_blank=False)


class ReasonSerializer(serializers.Serializer[Any]):
    reason = serializers.CharField(max_length=500, allow_blank=False)


class SuspensionSerializer(ReasonSerializer):
    suspended = serializers.BooleanField()


def account_access(account_id: UUID) -> dict[str, Any]:
    get_object_or_404(BillingAccount, pk=account_id)
    grant = ManualEntitlementGrant.objects.filter(account_id=account_id).first()
    return {
        "grant": grant_snapshot(grant),
        "effective": get_effective_entitlements(account_id),
        "subscription": subscription_snapshot(account_id),
    }


def subscription_snapshot(account_id: UUID) -> dict[str, Any] | None:
    subscription = Subscription.objects.filter(account_id=account_id).first()
    if subscription is None:
        return None
    return {
        "price": subscription.price_id,
        "seats": subscription.seats,
        "period_start": subscription.period_start,
        "period_end": subscription.period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


class AdminGrantView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, account_id: UUID) -> Response:
        return Response(account_access(account_id))

    def put(self, request: Request, account_id: UUID) -> Response:
        get_object_or_404(BillingAccount, pk=account_id)
        serializer = GrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        replace_grant(request.user, account_id, **serializer.validated_data)
        return Response(account_access(account_id))


class AdminGrantPreviewView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request, account_id: UUID) -> Response:
        get_object_or_404(BillingAccount, pk=account_id)
        serializer = GrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal = preview_grant(request.user, account_id, **serializer.validated_data)
        proposal["effective_after"] = {
            "source": "manual",
            "plan": proposal["plan"],
            "seat_limit": proposal["seat_limit"],
            "valid_until": proposal["expires_at"],
        }
        proposal["subscription"] = subscription_snapshot(account_id)
        return Response(proposal)


class AdminRevokeGrantView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request, account_id: UUID) -> Response:
        get_object_or_404(BillingAccount, pk=account_id)
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revoke_grant(request.user, account_id, **serializer.validated_data)
        return Response(account_access(account_id))


class AdminSuspensionView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request, account_id: UUID) -> Response:
        get_object_or_404(BillingAccount, pk=account_id)
        serializer = SuspensionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suspend_account(request.user, account_id, **serializer.validated_data)
        return Response(account_access(account_id))


class AuditSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = BillingAuditEvent
        fields = ["id", "actor", "action", "target", "details", "created_at"]


class AdminAccountAuditView(generics.ListAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = AuditSerializer
    pagination_class = BillingPagination

    def get_queryset(self) -> Any:
        account = get_object_or_404(BillingAccount, pk=self.kwargs["account_id"])
        return BillingAuditEvent.objects.filter(target=str(account.pk)).order_by(
            "-created_at", "-id"
        )
