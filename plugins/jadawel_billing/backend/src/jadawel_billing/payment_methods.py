from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .handlers import audit
from .models import BillingAccount, BillingOrder, PaymentMethod
from .payments import billing_mode
from .providers.moyasar import MoyasarClient


def _can_manage(actor: Any, account: BillingAccount) -> None:
    if not actor.is_authenticated or not actor.is_active:
        raise PermissionDenied()
    if actor.is_staff:
        return
    if account.responsible_user_id != actor.pk:
        raise PermissionDenied()


def save_payment_method(
    actor: Any,
    account: BillingAccount,
    *,
    provider_token: str | None = None,
    provider_payment_id: str,
    consent: bool,
    brand: str = "",
    last4: str = "",
    exp_month: int | None = None,
    exp_year: int | None = None,
) -> PaymentMethod:
    _can_manage(actor, account)
    if not consent:
        raise ValidationError({"consent": "required"})
    if provider_token is not None:
        provider_token = provider_token.strip()
        if not provider_token or len(provider_token) > 160:
            raise ValidationError({"provider_token": "invalid"})
    order = (
        BillingOrder.objects.filter(
            account=account,
            status="paid",
            payment_attempt__provider_payment_id=provider_payment_id,
        )
        .select_related("payment_attempt")
        .first()
    )
    if order is None:
        raise ValidationError({"provider_payment_id": "verified_payment_required"})
    client = MoyasarClient(
        secret_key=settings.JADAWEL_MOYASAR_SECRET_KEY,
        mode=billing_mode(),
    )
    payment = client.fetch(provider_payment_id)
    payment_source = payment.get("source") or {}
    provider_token = provider_token or payment_source.get("token")
    if not isinstance(provider_token, str):
        raise ValidationError({"provider_payment_id": "payment_token_missing"})
    provider_token = provider_token.strip()
    if not provider_token or len(provider_token) > 160:
        raise ValidationError({"provider_token": "invalid"})
    if (
        payment.get("status") not in {"paid", "captured"}
        or payment_source.get("token") != provider_token
    ):
        raise ValidationError({"provider_token": "payment_token_mismatch"})
    token = client.fetch_token(provider_token)
    if token.get("status") != "active":
        raise ValidationError({"provider_token": "token_not_active"})
    provider_brand = payment_source.get("brand") or payment_source.get("company") or ""
    provider_last4 = (
        payment_source.get("last4")
        or payment_source.get("last_four")
        or payment_source.get("lastFour")
        or ""
    )
    provider_exp_month = payment_source.get("month")
    provider_exp_year = payment_source.get("year")
    with transaction.atomic():
        method, _ = PaymentMethod.objects.update_or_create(
            provider_token=provider_token,
            defaults={
                "account": account,
                "brand": str(provider_brand or brand)[:40],
                "last4": str(provider_last4 or last4)[-4:],
                "exp_month": provider_exp_month or exp_month,
                "exp_year": provider_exp_year or exp_year,
                "consent_at": timezone.now(),
                "revoked_at": None,
            },
        )
        audit(
            actor,
            "payment_method.saved",
            account.pk,
            {"last4": method.last4, "brand": method.brand},
        )
    return method


@transaction.atomic
def revoke_payment_method(actor: Any, method: PaymentMethod) -> None:
    _can_manage(actor, method.account)
    method.revoked_at = timezone.now()
    method.save(update_fields=["revoked_at"])
    audit(
        actor,
        "payment_method.revoked",
        method.account_id,
        {"payment_method": method.pk},
    )


def list_payment_methods(actor: Any, account: BillingAccount):
    _can_manage(actor, account)
    return PaymentMethod.objects.filter(
        account=account, revoked_at__isnull=True
    ).order_by("-created_at")
