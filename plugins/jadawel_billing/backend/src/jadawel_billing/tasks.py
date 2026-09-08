from datetime import timedelta
from uuid import UUID

from celery import shared_task
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from jadawel_billing.errors import ProviderUnavailable
from jadawel_billing.models import BillingOrder, ProviderEvent
from jadawel_billing.payments import reconcile_order_system


@shared_task(name="jadawel_billing.reconcile_payments")  # type: ignore[untyped-decorator]
def reconcile_payments() -> None:
    now = timezone.now()
    # A worker can die after claiming an event. Requeue claims older than the
    # short lease so provider success is recoverable on the next beat tick.
    ProviderEvent.objects.filter(
        status="processing", updated_at__lt=now - timedelta(minutes=5)
    ).update(status="pending", error_code="worker_timeout", updated_at=now)
    for event in ProviderEvent.objects.filter(status="pending").order_by("created_at")[
        :100
    ]:
        with transaction.atomic():
            claimed = (
                ProviderEvent.objects.filter(pk=event.pk, status="pending")
                .select_for_update(skip_locked=True)
                .update(status="processing", updated_at=timezone.now())
            )
        if not claimed:
            continue
        order_query = Q(
            payment_attempt__provider_payment_id=event.payment_id, mode=event.mode
        )
        try:
            # This covers a rare provider payload that echoes Moyasar's
            # idempotency identifier instead of the provider payment id.
            order_query |= Q(payment_id=UUID(event.payment_id), mode=event.mode)
        except (ValueError, AttributeError):
            pass
        order = (
            BillingOrder.objects.select_related("account", "price", "payment_attempt")
            .filter(order_query)
            .first()
        )
        if order is None:
            # The webhook may precede the browser callback that binds the
            # provider identifier. Keep it retryable until that callback lands.
            ProviderEvent.objects.filter(pk=event.pk).update(
                status="pending",
                error_code="order_not_bound",
                attempts=F("attempts") + 1,
                updated_at=timezone.now(),
            )
            continue
        ProviderEvent.objects.filter(pk=event.pk).update(
            attempts=F("attempts") + 1, updated_at=timezone.now()
        )
        try:
            result = reconcile_order_system(order, provider_payment_id=event.payment_id)
            status = (
                "processed"
                if result.status == "paid"
                else "failed"
                if result.status == "failed"
                else "pending"
            )
            ProviderEvent.objects.filter(pk=event.pk).update(
                status=status,
                error_code="",
                updated_at=timezone.now(),
            )
        except ValidationError as exc:
            ProviderEvent.objects.filter(pk=event.pk).update(
                status="failed",
                error_code=str(exc.default_code)[:80],
                updated_at=timezone.now(),
            )
        except ProviderUnavailable as exc:
            ProviderEvent.objects.filter(pk=event.pk).update(
                status="pending",
                error_code=str(exc.default_code)[:80],
                updated_at=timezone.now(),
            )
        except APIException as exc:
            ProviderEvent.objects.filter(pk=event.pk).update(
                status="pending",
                error_code=str(exc.default_code)[:80],
                updated_at=timezone.now(),
            )

    # A successful browser payment may arrive before, or without, a webhook.
    # Revisit every pending order that already has a provider identifier.
    for order in BillingOrder.objects.filter(
        status="pending", payment_attempt__provider_payment_id__isnull=False
    ).select_related("account", "price", "payment_attempt")[:100]:
        try:
            reconcile_order_system(order)
        except APIException:
            continue
