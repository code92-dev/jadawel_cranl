from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone


def _provider_response(payload):
    response = Mock(status_code=200)
    response.json.return_value = payload
    return response


@pytest.mark.django_db
def test_team_seat_increase_is_prorated_idempotent_and_preserves_period(
    api_client, data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, Subscription
    from jadawel_organizations.models import Organization

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    payer, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(payer, kind="TEAM", responsible_user=payer)
    plan = create_plan(
        payer, code="team-seat-change", name="Team", kind="TEAM", available=True
    )
    price = create_price(
        payer, plan=plan, amount=12000, interval="MONTH", available=True
    )
    now = timezone.now()
    source_order = BillingOrder.objects.create(
        account=account,
        price=price,
        seats=2,
        amount=24000,
        currency="SAR",
        interval="MONTH",
        mode="test",
        status="paid",
    )
    subscription = Subscription.objects.create(
        account=account,
        price=price,
        seats=2,
        period_start=now - timedelta(days=10),
        period_end=now + timedelta(days=20),
        source_order=source_order,
        cancel_at_period_end=False,
    )
    Organization.objects.create(
        billing_account=account,
        name="Team",
        owner=payer,
        created_by=payer,
    )

    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    response = api_client.post(
        f"/api/billing/accounts/{account.pk}/subscription/seat-increase/",
        {"seats": 4},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["purpose"] == "seat_increase"
    assert 1 <= response.data["amount"] < price.amount * 2
    order_id = response.data["id"]

    repeated = api_client.post(
        f"/api/billing/accounts/{account.pk}/subscription/seat-increase/",
        {"seats": 4},
        format="json",
    )
    assert repeated.status_code == 200
    assert repeated.data["id"] == order_id

    provider_payment_id = "seat-increase-payment"
    remote = {
        "id": provider_payment_id,
        "status": "paid",
        "live": False,
        "amount": response.data["amount"],
        "currency": "SAR",
        "metadata": {"billing_order": order_id},
    }
    with patch("requests.get", return_value=_provider_response(remote)):
        verified = api_client.post(
            f"/api/billing/orders/{order_id}/verify/",
            {"provider_payment_id": provider_payment_id},
            format="json",
        )

    assert verified.status_code == 200
    assert verified.data["status"] == "paid"
    subscription.refresh_from_db()
    assert subscription.seats == 4
    assert subscription.period_start == now - timedelta(days=10)
    assert subscription.period_end == now + timedelta(days=20)
