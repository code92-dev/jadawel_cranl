import hmac
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel_billing.models import BillingOrder, PaymentAttempt, ProviderEvent
from jadawel_billing.payments import billing_mode


class EventData(serializers.Serializer[Any]):
    id = serializers.CharField(max_length=100)
    given_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False)


class EventInput(serializers.Serializer[Any]):
    id = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=60)
    live = serializers.BooleanField()
    # DRF's metaclass collects this provider field before the instance .data property.
    data = EventData()  # type: ignore[assignment]


class MoyasarWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        secret = getattr(settings, "JADAWEL_MOYASAR_WEBHOOK_SECRET", "")
        supplied = (
            request.data.get("secret_token") if isinstance(request.data, dict) else None
        )
        if (
            not secret
            or not isinstance(supplied, str)
            or not hmac.compare_digest(secret.encode(), supplied.encode())
        ):
            raise PermissionDenied()
        data = EventInput(data=request.data)
        data.is_valid(raise_exception=True)
        event = data.validated_data
        mode = billing_mode()
        if event["live"] != (mode == "live"):
            raise ValidationError({"live": "environment_mismatch"})
        if not event["type"].startswith("payment_"):
            return Response(status=202)
        # Store only identifiers, never card details or the shared secret. The
        # scheduled reconciler is durable even if queue dispatch is unavailable.
        provider_payment_id = event["data"]["id"]
        provider_event, _ = ProviderEvent.objects.get_or_create(
            event_id=event["id"],
            mode=mode,
            defaults={"payment_id": provider_payment_id, "event_type": event["type"]},
        )
        # Bind only the provider identifier from an authenticated event. The
        # scheduled verifier still fetches the payment and validates all
        # amount, currency, metadata and status fields before granting access.
        metadata = event["data"].get("metadata") or {}
        order_value = metadata.get("billing_order")
        order = None
        if isinstance(order_value, str):
            try:
                order = BillingOrder.objects.filter(
                    pk=UUID(order_value), mode=mode
                ).first()
            except ValueError:
                order = None
        if order is None and event["data"].get("given_id"):
            order = BillingOrder.objects.filter(
                payment_id=event["data"]["given_id"], mode=mode
            ).first()
        if order is not None:
            with transaction.atomic():
                attempt = PaymentAttempt.objects.select_for_update().get(order=order)
                if attempt.provider_payment_id in (None, provider_payment_id):
                    if attempt.provider_payment_id is None:
                        try:
                            attempt.provider_mode = mode
                            attempt.provider_payment_id = provider_payment_id
                            attempt.save(
                                update_fields=[
                                    "provider_mode",
                                    "provider_payment_id",
                                    "updated_at",
                                ]
                            )
                        except IntegrityError:
                            pass
                elif provider_event.error_code == "":
                    provider_event.error_code = "provider_id_conflict"
                    provider_event.save(update_fields=["error_code", "updated_at"])
        return Response(status=202)
