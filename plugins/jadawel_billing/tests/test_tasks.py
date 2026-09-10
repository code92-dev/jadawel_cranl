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


@pytest.mark.django_db
def test_pending_event_backlog_rotates_and_ignores_inactive_mode(settings):
    from jadawel_billing.models import ProviderEvent
    from jadawel_billing.tasks import reconcile_payments

    settings.JADAWEL_BILLING_MODE = "test"
    inactive = ProviderEvent.objects.create(
        event_id="live", mode="live", payment_id="live", event_type="payment_paid"
    )
    events = [
        ProviderEvent.objects.create(
            event_id=f"event-{i}",
            mode="test",
            payment_id=f"missing-{i}",
            event_type="payment_paid",
        )
        for i in range(101)
    ]
    reconcile_payments.run()
    events[-1].refresh_from_db()
    assert events[-1].attempts == 0
    reconcile_payments.run()
    events[-1].refresh_from_db()
    inactive.refresh_from_db()
    assert events[-1].attempts == 1
    assert inactive.attempts == 0
    assert ProviderEvent.objects.filter(attempts=1).count() == 101


@pytest.mark.django_db
def test_order_retries_rotate_after_provider_failure(data_fixture, settings):
    from jadawel_billing.errors import ProviderUnavailable
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, PaymentAttempt
    from jadawel_billing.tasks import reconcile_payments

    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    plan = create_plan(admin, code="retry", name="Retry", kind="TEAM")
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    orders = []
    for index in range(102):
        account = create_account(admin, kind="TEAM", responsible_user=admin)
        order = BillingOrder.objects.create(
            account=account,
            price=price,
            amount=5000,
            interval="MONTH",
            mode="live" if index == 0 else "test",
        )
        PaymentAttempt.objects.create(
            order=order,
            given_id=order.payment_id,
            provider_payment_id=f"provider-{index}",
            provider_mode=order.mode,
        )
        orders.append(order)
    with patch(
        "jadawel_billing.tasks.reconcile_order_system",
        side_effect=ProviderUnavailable(),
    ) as reconcile:
        reconcile_payments.run()
        first = {call.args[0].pk for call in reconcile.call_args_list}
        assert len(first) == 100
        assert orders[0].pk not in first
        assert orders[-1].pk not in first
        reconcile.reset_mock()
        reconcile_payments.run()
        assert reconcile.call_args_list[0].args[0].pk == orders[-1].pk


@pytest.mark.django_db
def test_renewal_stops_after_the_configured_grace_window(data_fixture, settings):
    from datetime import timedelta

    from django.utils import timezone

    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, Subscription
    from jadawel_billing.subscriptions import renew_due_subscriptions

    settings.JADAWEL_BILLING_MODE = "test"
    settings.JADAWEL_BILLING_GRACE_DAYS = 7
    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin, code="renewal-cutoff", name="Renewal cutoff", kind="INDIVIDUAL"
    )
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    now = timezone.now()
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        seats=1,
        amount=price.amount,
        currency=price.currency,
        interval=price.interval,
        mode="test",
        status="paid",
    )
    subscription = Subscription.objects.create(
        account=account,
        price=price,
        seats=1,
        period_start=now - timedelta(days=38),
        period_end=now - timedelta(days=8),
        source_order=order,
        status=Subscription.Status.GRACE,
        cancel_at_period_end=False,
        next_retry_at=now - timedelta(minutes=1),
    )

    with patch("jadawel_billing.subscriptions.MoyasarClient") as client:
        assert renew_due_subscriptions() == 0
        client.assert_not_called()

    subscription.refresh_from_db()
    assert subscription.status == Subscription.Status.CANCELED
    assert subscription.next_retry_at is None
