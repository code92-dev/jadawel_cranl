import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_admin_creates_and_lists_personal_billing_account(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token(is_staff=True)
    customer = data_fixture.create_user()
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    response = api_client.post(
        "/api/billing/admin/accounts/",
        {"kind": "INDIVIDUAL", "responsible_user": customer.id},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["kind"] == "INDIVIDUAL"
    listing = api_client.get("/api/billing/admin/accounts/")
    assert listing.status_code == 200
    assert listing.data["results"][0]["id"] == response.data["id"]


@pytest.mark.django_db
def test_admin_versions_a_plan_without_rewriting_the_previous_price(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    plan = api_client.post(
        "/api/billing/admin/plans/",
        {"code": "individual", "name": "Individual", "kind": "INDIVIDUAL"},
        format="json",
    )
    assert plan.status_code == 201
    url = f"/api/billing/admin/plans/{plan.data['id']}/prices/"
    price = api_client.post(url, {"amount": 5000, "interval": "MONTH"}, format="json")
    assert price.status_code == 201
    next_price = api_client.post(
        url, {"amount": 7500, "interval": "MONTH"}, format="json"
    )
    assert next_price.status_code == 201
    listed = api_client.get(url)
    assert [p["amount"] for p in listed.data["results"]] == [7500, 5000]
    assert (
        api_client.patch(
            f"/api/billing/admin/prices/{price.data['id']}/",
            {"amount": 1},
            format="json",
        ).status_code
        == 400
    )
    assert (
        api_client.patch(
            f"/api/billing/admin/prices/{price.data['id']}/",
            {"available": False},
            format="json",
        ).status_code
        == 200
    )
    assert api_client.get(url).data["results"][1]["amount"] == 5000


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["accounts/", "plans/"])
def test_billing_administration_denies_non_staff(api_client, data_fixture, path):
    _, token = data_fixture.create_user_and_token()
    url = "/api/billing/admin/" + path
    assert api_client.get(url).status_code == 401
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    assert api_client.get(url).status_code == 403
    assert api_client.post(url, {}, format="json").status_code == 403


@pytest.mark.django_db
def test_admin_provider_health_is_safe_when_moyasar_is_not_configured(
    api_client, data_fixture, settings
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    settings.JADAWEL_BILLING_MODE = "test"
    settings.JADAWEL_MOYASAR_SECRET_KEY = ""
    settings.JADAWEL_MOYASAR_PUBLISHABLE_KEY = ""
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    response = api_client.get("/api/billing/admin/provider-health/")

    assert response.status_code == 200
    assert response.data == {
        "mode": "test",
        "status": "not_configured",
        "configured": False,
    }


@pytest.mark.django_db
def test_admin_lists_and_controls_subscription_renewal(api_client, data_fixture):
    from datetime import timedelta

    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, Subscription

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(
        admin,
        code="admin-renewal",
        name="Admin renewal",
        kind="INDIVIDUAL",
        available=True,
    )
    price = create_price(
        admin, plan=plan, amount=5000, interval="MONTH", available=True
    )
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
        period_start=timezone.now(),
        period_end=timezone.now() + timedelta(days=30),
        source_order=order,
        cancel_at_period_end=False,
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    listing = api_client.get("/api/billing/admin/subscriptions/")
    assert listing.status_code == 200
    assert listing.data["results"][0]["id"] == subscription.id
    assert listing.data["results"][0]["owner_email"] == admin.email

    updated = api_client.patch(
        f"/api/billing/admin/subscriptions/{subscription.pk}/",
        {"cancel_at_period_end": True},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["cancel_at_period_end"] is True


@pytest.mark.django_db
def test_duplicate_personal_account_is_rejected_but_team_accounts_are_independent(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    user = data_fixture.create_user()
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    url = "/api/billing/admin/accounts/"
    payload = {"kind": "INDIVIDUAL", "responsible_email": user.email}
    assert api_client.post(url, payload, format="json").status_code == 201
    assert api_client.post(url, payload, format="json").status_code == 400
    payload["kind"] = "TEAM"
    assert api_client.post(url, payload, format="json").status_code == 201
    assert api_client.post(url, payload, format="json").status_code == 201


@pytest.mark.django_db
def test_catalogue_rejects_invalid_price_and_defaults_to_not_for_sale(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    plan = api_client.post(
        "/api/billing/admin/plans/",
        {
            "code": "team",
            "name": "Team",
            "kind": "TEAM",
        },
        format="json",
    )
    assert plan.data["available"] is False
    url = f"/api/billing/admin/plans/{plan.data['id']}/prices/"
    assert (
        api_client.post(
            url, {"amount": -1, "interval": "MONTH"}, format="json"
        ).status_code
        == 400
    )
    assert (
        api_client.post(
            url, {"amount": 100, "interval": "DAY"}, format="json"
        ).status_code
        == 400
    )
    price = api_client.post(url, {"amount": 100, "interval": "YEAR"}, format="json")
    assert price.data["available"] is False
    assert price.data["currency"] == "SAR"


@pytest.mark.django_db
def test_direct_handler_rejects_non_staff(data_fixture):
    from jadawel_billing.handlers import create_account
    from rest_framework.exceptions import PermissionDenied

    user = data_fixture.create_user()
    with pytest.raises(PermissionDenied):
        create_account(user, kind="TEAM", responsible_user=user)


@pytest.mark.django_db
def test_admin_records_and_lists_external_payment(api_client, data_fixture):
    from jadawel_billing.handlers import create_account

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    paid_at = timezone.now().isoformat()
    response = api_client.post(
        "/api/billing/admin/external-payments/",
        {
            "account": str(account.pk),
            "amount": 2500,
            "reference": "bank-transfer-1",
            "paid_at": paid_at,
            "notes": "Manual settlement",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["account"] == str(account.pk)
    assert response.data["amount"] == 2500
    assert response.data["reference"] == "bank-transfer-1"
    listing = api_client.get("/api/billing/admin/external-payments/")
    assert listing.status_code == 200
    assert listing.data["results"][0]["reference"] == "bank-transfer-1"


@pytest.mark.django_db
def test_external_payment_reference_is_idempotent_but_immutable(
    api_client, data_fixture
):
    from jadawel_billing.handlers import create_account

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    paid_at = timezone.now().isoformat()
    payload = {
        "account": str(account.pk),
        "amount": 2500,
        "reference": "bank-transfer-idempotent",
        "paid_at": paid_at,
        "notes": "Manual settlement",
    }
    first = api_client.post(
        "/api/billing/admin/external-payments/", payload, format="json"
    )
    repeated = api_client.post(
        "/api/billing/admin/external-payments/", payload, format="json"
    )
    changed = api_client.post(
        "/api/billing/admin/external-payments/",
        {**payload, "amount": 2600},
        format="json",
    )

    assert first.status_code == 201
    assert repeated.status_code == 201
    assert repeated.data["id"] == first.data["id"]
    assert changed.status_code == 400
    assert changed.data["reference"] == "already_used_with_different_details"
