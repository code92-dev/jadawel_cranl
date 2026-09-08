import uuid

from django.conf import settings
from django.db import models


class BillingAccount(models.Model):
    class Kind(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL"
        TEAM = "TEAM"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    suspended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["responsible_user"],
                condition=models.Q(kind="INDIVIDUAL"),
                name="billing_one_personal_account",
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["INDIVIDUAL", "TEAM"]),
                name="billing_account_valid_kind",
            ),
        ]


class Plan(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=BillingAccount.Kind.choices)
    available = models.BooleanField(default=False)


class PlanPrice(models.Model):
    class Interval(models.TextChoices):
        MONTH = "MONTH"
        YEAR = "YEAR"

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="prices")
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="SAR", editable=False)
    interval = models.CharField(max_length=5, choices=Interval.choices)
    available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=1), name="billing_price_positive_amount"
            )
        ]


class BillingAuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=60)
    target = models.CharField(max_length=80)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class ManualEntitlementGrant(models.Model):
    account = models.OneToOneField(
        BillingAccount, on_delete=models.PROTECT, related_name="manual_grant"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    seat_limit = models.PositiveIntegerField()
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=500)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(seat_limit__gte=1),
                name="billing_grant_positive_seats",
            ),
            models.CheckConstraint(
                condition=models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=models.F("starts_at")),
                name="billing_grant_valid_period",
            ),
        ]


class BillingOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(BillingAccount, on_delete=models.PROTECT)
    price = models.ForeignKey(PlanPrice, on_delete=models.PROTECT)
    seats = models.PositiveIntegerField(default=1)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="SAR")
    interval = models.CharField(max_length=5, choices=PlanPrice.Interval.choices)
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    mode = models.CharField(max_length=4, default="test")
    status = models.CharField(max_length=12, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account"],
                condition=models.Q(status="pending"),
                name="billing_one_pending_order",
            ),
            models.CheckConstraint(
                condition=models.Q(seats__gte=1), name="billing_order_positive_seats"
            ),
        ]


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        INITIATED = "initiated"
        AUTHORIZED = "authorized"
        PAID = "paid"
        FAILED = "failed"

    order = models.OneToOneField(
        BillingOrder, on_delete=models.PROTECT, related_name="payment_attempt"
    )
    given_id = models.UUIDField(unique=True)
    provider_mode = models.CharField(max_length=4, default="test", editable=False)
    provider_payment_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default="pending")
    failure_code = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider_mode", "provider_payment_id"],
                condition=models.Q(provider_payment_id__isnull=False),
                name="billing_unique_provider_payment_by_mode",
            )
        ]


class Subscription(models.Model):
    account = models.OneToOneField(BillingAccount, on_delete=models.PROTECT)
    price = models.ForeignKey(PlanPrice, on_delete=models.PROTECT)
    seats = models.PositiveIntegerField()
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=True)
    source_order = models.OneToOneField(BillingOrder, on_delete=models.PROTECT)


class ProviderEvent(models.Model):
    event_id = models.CharField(max_length=100)
    mode = models.CharField(max_length=4)
    payment_id = models.CharField(max_length=100)
    event_type = models.CharField(max_length=60)
    status = models.CharField(max_length=12, default="pending")
    attempts = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_id", "mode"], name="billing_unique_provider_event"
            )
        ]
