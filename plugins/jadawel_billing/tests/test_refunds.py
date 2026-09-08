from unittest.mock import patch

import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(JADAWEL_MOYASAR_SECRET_KEY="sk_test_fixture")
def test_refund_is_single_operation_and_keeps_its_amount_on_retry(data_fixture):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, PaymentAttempt
    from jadawel_billing.refunds import refund_order

    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(admin, code="refunds", name="Refunds", kind="INDIVIDUAL")
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        amount=5000,
        interval="MONTH",
        mode="test",
        status="paid",
    )
    PaymentAttempt.objects.create(
        order=order,
        given_id=order.payment_id,
        provider_mode="test",
        provider_payment_id="payment-1",
    )

    failed = {"status": "failed"}
    succeeded = {"status": "refunded", "id": "refund-1"}
    with patch(
        "jadawel_billing.refunds.MoyasarClient.refund",
        side_effect=[failed, succeeded],
    ) as provider_refund:
        first = refund_order(admin, order, amount=2000, reason="Duplicate test")
        second = refund_order(admin, order, amount=2000, reason="Retry test")

    assert first.pk == second.pk
    assert second.status == "succeeded"
    assert second.amount == 2000
    assert provider_refund.call_args_list[0].args == ("payment-1", 2000)
    assert provider_refund.call_args_list[1].args == ("payment-1", 2000)


@pytest.mark.django_db
@override_settings(JADAWEL_MOYASAR_SECRET_KEY="sk_test_fixture")
def test_uncertain_refund_blocks_a_duplicate_provider_call(data_fixture):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, PaymentAttempt
    from jadawel_billing.refunds import refund_order
    from rest_framework.exceptions import ValidationError

    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin, code="refunds-uncertain", name="Refunds", kind="INDIVIDUAL"
    )
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        amount=5000,
        interval="MONTH",
        mode="test",
        status="paid",
    )
    PaymentAttempt.objects.create(
        order=order,
        given_id=order.payment_id,
        provider_mode="test",
        provider_payment_id="payment-uncertain",
    )

    with patch(
        "jadawel_billing.refunds.MoyasarClient.refund",
        side_effect=TimeoutError("provider timeout"),
    ) as provider_refund:
        with pytest.raises(TimeoutError):
            refund_order(admin, order, amount=2000, reason="Uncertain test")
        with pytest.raises(ValidationError, match="already_processing"):
            refund_order(admin, order, amount=2000, reason="Retry test")

    assert provider_refund.call_count == 1
