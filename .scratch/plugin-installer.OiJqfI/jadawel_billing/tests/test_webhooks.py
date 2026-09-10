from unittest.mock import Mock, patch

import pytest


@pytest.mark.django_db
def test_webhook_authenticates_and_deduplicates_without_trusting_payment_body(
    api_client, settings
):
    settings.JADAWEL_MOYASAR_WEBHOOK_SECRET = "test_webhook_secret"
    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    payload = {
        "id": "event-1",
        "type": "payment_paid",
        "live": False,
        "secret_token": "wrong",
        "data": {"id": "720878ec-d1d3-4f72-9056-191683faa872", "status": "paid"},
    }
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 403
    )
    payload["secret_token"] = "test_webhook_secret"
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 202
    )
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 202
    )
    payload["live"] = True
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_authenticated_webhook_binds_order_for_callback_free_recovery(
    api_client, data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt
    from jadawel_billing.payments import create_order

    settings.JADAWEL_MOYASAR_WEBHOOK_SECRET = "test_webhook_secret"
    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin,
        code="webhook-recovery",
        name="Individual",
        kind="INDIVIDUAL",
        available=True,
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
    order = create_order(admin, account, price, 1)
    payload = {
        "id": "event-recovery",
        "type": "payment_paid",
        "live": False,
        "secret_token": "test_webhook_secret",
        "data": {
            "id": "provider-recovery",
            "metadata": {"billing_order": str(order.pk)},
        },
    }
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 202
    )
    assert (
        PaymentAttempt.objects.get(order=order).provider_payment_id
        == "provider-recovery"
    )
    response = Mock(status_code=200)
    response.json.return_value = {
        "id": "provider-recovery",
        "status": "paid",
        "amount": order.amount,
        "currency": order.currency,
        "metadata": {"billing_order": str(order.pk)},
    }
    from jadawel_billing.tasks import reconcile_payments

    with patch("requests.get", return_value=response):
        reconcile_payments.run()
    order.refresh_from_db()
    assert order.status == "paid"


@pytest.mark.django_db
def test_live_webhook_binding_keeps_provider_mode_isolated(
    api_client, data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt
    from jadawel_billing.payments import create_order

    settings.JADAWEL_MOYASAR_WEBHOOK_SECRET = "live_webhook_secret"
    settings.JADAWEL_BILLING_MODE = "live"
    settings.JADAWEL_BILLING_LIVE_ENABLED = True
    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_live_fixture"
    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin, code="webhook-live", name="Individual", kind="INDIVIDUAL", available=True
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
    order = create_order(admin, account, price, 1)
    payload = {
        "id": "event-live",
        "type": "payment_paid",
        "live": True,
        "secret_token": "live_webhook_secret",
        "data": {
            "id": "provider-live",
            "metadata": {"billing_order": str(order.pk)},
        },
    }
    assert (
        api_client.post(
            "/api/billing/moyasar/webhook/", payload, format="json"
        ).status_code
        == 202
    )
    assert PaymentAttempt.objects.get(order=order).provider_mode == "live"
