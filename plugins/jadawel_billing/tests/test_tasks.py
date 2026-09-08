from unittest.mock import Mock, patch

import pytest


@pytest.mark.django_db
def test_reconciler_processes_a_payment_without_using_the_payer_session(
    data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt, ProviderEvent
    from jadawel_billing.payments import create_order
    from jadawel_billing.tasks import reconcile_payments

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    payer = data_fixture.create_user(is_active=False)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=payer)
    plan = create_plan(
        admin,
        code="individual",
        name="Individual",
        kind="INDIVIDUAL",
        available=True,
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
    # Directly construct the order because an inactive payer cannot start a new checkout.
    payer.is_active = True
    payer.save(update_fields=["is_active"])
    order = create_order(payer, account, price, 1)
    payer.is_active = False
    payer.save(update_fields=["is_active"])
    PaymentAttempt.objects.filter(order=order).update(
        provider_payment_id="provider-payment-1"
    )
    event = ProviderEvent.objects.create(
        event_id="event-1",
        mode="test",
        payment_id="provider-payment-1",
        event_type="payment_paid",
    )
    response = Mock(status_code=200)
    response.json.return_value = {
        "id": "provider-payment-1",
        "status": "paid",
        "live": False,
        "amount": order.amount,
        "currency": order.currency,
        "metadata": {"billing_order": str(order.pk)},
    }
    with patch("requests.get", return_value=response):
        reconcile_payments.run()
    event.refresh_from_db()
    order.refresh_from_db()
    assert event.status == "processed"
    assert order.status == "paid"


@pytest.mark.django_db
def test_reconciler_marks_a_provider_mismatch_failed(data_fixture, settings):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt, ProviderEvent
    from jadawel_billing.payments import create_order
    from jadawel_billing.tasks import reconcile_payments

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    payer = data_fixture.create_user()
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=payer)
    plan = create_plan(
        admin,
        code="individual",
        name="Individual",
        kind="INDIVIDUAL",
        available=True,
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
    order = create_order(payer, account, price, 1)
    PaymentAttempt.objects.filter(order=order).update(
        provider_payment_id="provider-payment-mismatch"
    )
    event = ProviderEvent.objects.create(
        event_id="event-mismatch",
        mode="test",
        payment_id="provider-payment-mismatch",
        event_type="payment_paid",
    )
    response = Mock(status_code=200)
    response.json.return_value = {
        "id": "provider-payment-mismatch",
        "status": "paid",
        "live": False,
        "amount": 1,
        "currency": order.currency,
        "metadata": {"billing_order": str(order.pk)},
    }
    with patch("requests.get", return_value=response):
        reconcile_payments.run()
    event.refresh_from_db()
    assert event.status == "failed"
    assert event.error_code == "invalid"


@pytest.mark.django_db
def test_webhook_before_callback_stays_retryable(data_fixture, settings):
    from jadawel_billing.models import ProviderEvent
    from jadawel_billing.tasks import reconcile_payments

    settings.JADAWEL_BILLING_MODE = "test"
    event = ProviderEvent.objects.create(
        event_id="event-before-callback",
        mode="test",
        payment_id="provider-not-bound",
        event_type="payment_paid",
    )
    reconcile_payments.run()
    event.refresh_from_db()
    assert event.status == "pending"
    assert event.error_code == "order_not_bound"
