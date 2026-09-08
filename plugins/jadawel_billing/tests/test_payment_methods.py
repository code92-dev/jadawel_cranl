from unittest.mock import Mock, patch

import pytest
from django.db import connection
from rest_framework.exceptions import ValidationError


def _provider_response(payload):
    response = Mock(status_code=200)
    response.json.return_value = payload
    return response


@pytest.mark.django_db(transaction=True)
def test_payment_method_requires_active_token_bound_to_paid_payment(
    data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt
    from jadawel_billing.payment_methods import save_payment_method
    from jadawel_billing.payments import create_order

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin, code="method", name="Method", kind="INDIVIDUAL", available=True
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
    order = create_order(admin, account, price, 1)
    order.status = "paid"
    order.save(update_fields=["status"])
    PaymentAttempt.objects.filter(order=order).update(
        provider_payment_id="provider-payment"
    )
    token = {
        "id": "token_active",
        "status": "active",
        "brand": "visa",
        "last_four": "1111",
    }
    payment = {
        "id": "provider-payment",
        "status": "paid",
        "source": {"token": "token_active"},
    }

    def provider_get(url, **kwargs):
        assert not connection.in_atomic_block
        return _provider_response(token if "/tokens/" in url else payment)

    with patch("requests.get", side_effect=provider_get):
        method = save_payment_method(
            admin,
            account,
            provider_token="token_active",
            provider_payment_id="provider-payment",
            consent=True,
        )
    assert method.last4 == ""

    inactive = {**token, "id": "token_inactive", "status": "initiated"}
    with patch("requests.get", return_value=_provider_response(inactive)):
        with pytest.raises(ValidationError):
            save_payment_method(
                admin,
                account,
                provider_token="token_inactive",
                provider_payment_id="provider-payment",
                consent=True,
            )
