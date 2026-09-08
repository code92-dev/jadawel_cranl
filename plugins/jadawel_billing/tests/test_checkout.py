from unittest.mock import Mock, patch

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payment_override,expected_status",
    [
        ({}, 200),
        ({"amount": 1}, 400),
        ({"currency": "USD"}, 400),
        ({"metadata": {"billing_order": "another-order"}}, 400),
        ({"status": "initiated"}, 200),
        ({"status": "authorized"}, 200),
        ({"status": "captured"}, 200),
        ({"status": "failed", "failure_code": "insufficient_funds"}, 200),
    ],
)
def test_individual_subscription_activates_only_after_provider_verification(
    api_client, data_fixture, settings, payment_override, expected_status
):
    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_MOYASAR_PUBLISHABLE_KEY = "pk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin, admin_token = data_fixture.create_user_and_token(is_staff=True)
    user, token = data_fixture.create_user_and_token(is_staff=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {admin_token}")
    account = api_client.post(
        "/api/billing/admin/accounts/",
        {
            "kind": "INDIVIDUAL",
            "responsible_user": user.id,
        },
        format="json",
    ).data
    plan = api_client.post(
        "/api/billing/admin/plans/",
        {
            "code": "individual",
            "name": "Individual",
            "kind": "INDIVIDUAL",
            "available": True,
        },
        format="json",
    ).data
    price = api_client.post(
        f"/api/billing/admin/plans/{plan['id']}/prices/",
        {
            "amount": 5000,
            "interval": "MONTH",
            "available": True,
        },
        format="json",
    ).data
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    response = api_client.post(
        "/api/billing/orders/",
        {
            "account": account["id"],
            "price": price["id"],
            "seats": 1,
        },
        format="json",
    )
    assert response.status_code == 201
    order = response.data
    assert order["amount"] == 5000
    assert order["status"] == "pending"
    provider_payment_id = "provider-payment-1"
    verified_payment = {
        "id": provider_payment_id,
        "status": "paid",
        "live": False,
        "amount": 5000,
        "currency": "SAR",
        "metadata": {"billing_order": order["id"]},
    }
    remote = Mock(status_code=200)
    verified_payment.update(payment_override)
    remote.json.return_value = verified_payment
    with patch("requests.get", return_value=remote):
        verified = api_client.post(
            f"/api/billing/orders/{order['id']}/verify/",
            {"provider_payment_id": provider_payment_id},
            format="json",
        )
    assert verified.status_code == expected_status
    account_view = api_client.get(f"/api/billing/accounts/{account['id']}/")
    if payment_override:
        if payment_override.get("status") == "captured":
            assert verified.data["status"] == "paid"
            assert account_view.data["effective"]["source"] == "paid"
            return
        assert account_view.data["effective"]["source"] == "restricted"
        assert account_view.data["subscription"] is None
        if payment_override.get("status") == "failed":
            assert (
                api_client.post(
                    "/api/billing/orders/",
                    {
                        "account": account["id"],
                        "price": price["id"],
                        "seats": 1,
                    },
                    format="json",
                ).status_code
                == 201
            )
        return
    assert verified.data["status"] == "paid"
    assert account_view.data["effective"]["source"] == "paid"
    assert account_view.data["subscription"]["seats"] == 1
    assert verified.data["receipt"]["provider_payment_id"] == provider_payment_id
    assert verified.data["receipt"]["period_end"] is not None
    with patch("requests.get", return_value=remote):
        assert (
            api_client.post(
                f"/api/billing/orders/{order['id']}/verify/",
                {"provider_payment_id": provider_payment_id},
                format="json",
            ).status_code
            == 200
        )
    assert (
        api_client.get(f"/api/billing/accounts/{account['id']}/").data["subscription"]
        == account_view.data["subscription"]
    )


@pytest.mark.django_db
def test_checkout_options_hide_team_until_organizations_is_loaded(
    api_client, data_fixture, settings
):
    import jadawel_billing.entitlements as entitlements
    from jadawel_billing.handlers import create_account, create_plan, create_price

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_MOYASAR_PUBLISHABLE_KEY = "pk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    user, token = data_fixture.create_user_and_token(is_staff=True)
    create_account(user, kind="INDIVIDUAL", responsible_user=user)
    team_plan = create_plan(
        user, code="team-hidden", name="Team", kind="TEAM", available=True
    )
    create_price(user, plan=team_plan, amount=5000, interval="MONTH", available=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    previous = entitlements._team_provisioner
    entitlements._team_provisioner = None
    try:
        response = api_client.get("/api/billing/checkout/")
    finally:
        entitlements._team_provisioner = previous
    assert response.status_code == 200
    assert response.data["team_available"] is False
    assert response.data["prices"] == []


@pytest.mark.django_db
def test_staff_can_reconcile_an_order_when_payer_is_no_longer_active(
    api_client, data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.payments import create_order

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin, admin_token = data_fixture.create_user_and_token(is_staff=True)
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
    payer.is_active = False
    payer.save(update_fields=["is_active"])
    remote = Mock(status_code=200)
    remote.json.return_value = {
        "id": "provider-payment-2",
        "status": "paid",
        "live": False,
        "amount": order.amount,
        "currency": order.currency,
        "metadata": {"billing_order": str(order.pk)},
    }
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {admin_token}")
    with patch("requests.get", return_value=remote):
        response = api_client.post(
            f"/api/billing/admin/orders/{order.pk}/reconcile/",
            {"provider_payment_id": "provider-payment-2"},
            format="json",
        )
    assert response.status_code == 200
    assert response.data["status"] == "paid"


@pytest.mark.django_db
def test_invalid_provider_id_does_not_poison_order_for_a_later_retry(
    api_client, data_fixture, settings
):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import PaymentAttempt
    from jadawel_billing.payments import create_order

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    user, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(user, kind="INDIVIDUAL", responsible_user=user)
    plan = create_plan(
        user,
        code="individual-retry",
        name="Individual",
        kind="INDIVIDUAL",
        available=True,
    )
    price = create_price(user, plan=plan, amount=5000, interval="MONTH", available=True)
    order = create_order(user, account, price, 1)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    missing = Mock(status_code=404)
    with patch("requests.get", return_value=missing):
        assert (
            api_client.post(
                f"/api/billing/orders/{order.pk}/verify/",
                {"provider_payment_id": "bad-payment"},
                format="json",
            ).status_code
            == 503
        )
    assert PaymentAttempt.objects.get(order=order).provider_payment_id is None
    remote = Mock(status_code=200)
    remote.json.return_value = {
        "id": "good-payment",
        "status": "paid",
        "live": False,
        "amount": order.amount,
        "currency": order.currency,
        "metadata": {"billing_order": str(order.pk)},
    }
    with patch("requests.get", return_value=remote):
        response = api_client.post(
            f"/api/billing/orders/{order.pk}/verify/",
            {"provider_payment_id": "good-payment"},
            format="json",
        )
    assert response.status_code == 200
    assert response.data["status"] == "paid"
