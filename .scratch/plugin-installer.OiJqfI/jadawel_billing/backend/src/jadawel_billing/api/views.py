from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser

from jadawel_billing.handlers import (
    create_account,
    create_plan,
    create_price,
    set_availability,
)
from jadawel_billing.models import BillingAccount, Plan, PlanPrice


class BillingPagination(PageNumberPagination):
    page_size = 25


class AccountSerializer(serializers.ModelSerializer[Any]):
    responsible_email = serializers.EmailField(write_only=True, required=False)
    owner_email = serializers.EmailField(
        source="responsible_user.email", read_only=True
    )

    class Meta:
        model = BillingAccount
        fields = [
            "id",
            "kind",
            "responsible_user",
            "responsible_email",
            "owner_email",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"responsible_user": {"required": False}}

    def validate(self, attrs: Any) -> Any:
        email = attrs.pop("responsible_email", None)
        if email and "responsible_user" in attrs:
            raise serializers.ValidationError({"responsible_email": "choose_one_owner"})
        if email:
            user = (
                get_user_model()
                .objects.filter(email__iexact=email, is_active=True)
                .first()
            )
            if user is None:
                raise serializers.ValidationError(
                    {"responsible_email": "user_not_found"}
                )
            attrs["responsible_user"] = user
        if "responsible_user" not in attrs:
            raise serializers.ValidationError({"responsible_email": "required"})
        if not attrs["responsible_user"].is_active:
            raise serializers.ValidationError({"responsible_user": "inactive"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        return create_account(self.context["request"].user, **validated_data)


class AdminAccountsView(generics.ListCreateAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = AccountSerializer
    pagination_class = BillingPagination
    queryset = BillingAccount.objects.order_by("-created_at", "id")


class PlanSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = Plan
        fields = ["id", "code", "name", "kind", "available"]

    def create(self, validated_data: dict[str, Any]) -> Any:
        return create_plan(self.context["request"].user, **validated_data)


class PriceSerializer(serializers.ModelSerializer[Any]):
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = PlanPrice
        fields = ["id", "amount", "currency", "interval", "available", "created_at"]
        read_only_fields = ["id", "currency", "created_at"]

    def create(self, validated_data: dict[str, Any]) -> Any:
        plan = get_object_or_404(Plan, pk=self.context["view"].kwargs["plan_id"])
        return create_price(self.context["request"].user, plan=plan, **validated_data)


class AdminPlansView(generics.ListCreateAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = PlanSerializer
    pagination_class = BillingPagination
    queryset = Plan.objects.order_by("id")


class AdminPricesView(generics.ListCreateAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = PriceSerializer
    pagination_class = BillingPagination

    def get_queryset(self) -> Any:
        plan = get_object_or_404(Plan, pk=self.kwargs["plan_id"])
        return plan.prices.order_by("-created_at", "-id")


class AvailabilitySerializer(serializers.Serializer[Any]):
    available = serializers.BooleanField()

    def to_internal_value(self, data: Any) -> Any:
        if set(data) != {"available"}:
            raise serializers.ValidationError(
                {"non_field_errors": ["availability_only"]}
            )
        return super().to_internal_value(data)

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        return set_availability(
            self.context["request"].user, instance, **validated_data
        )


class AdminPriceView(generics.UpdateAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = AvailabilitySerializer
    queryset = PlanPrice.objects.all()
    http_method_names = ["patch", "options"]


class AdminPlanView(generics.UpdateAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = AvailabilitySerializer
    http_method_names = ["patch", "options"]
    queryset = Plan.objects.all()
