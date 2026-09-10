from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_grant_expiry_and_suspension_precedence(data_fixture):
    from jadawel_billing.entitlements import get_effective_entitlements
    from jadawel_billing.grants import replace_grant, suspend_account
    from jadawel_billing.handlers import create_account, create_plan

    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="TEAM", responsible_user=admin)
    plan = create_plan(admin, code="team", name="Team", kind="TEAM")
    start = timezone.now()
    end = start + timedelta(days=1)
    replace_grant(
        admin,
        account.pk,
        plan=plan,
        seat_limit=5,
        starts_at=start,
        expires_at=end,
        reason="Test grant",
    )
    assert (
        get_effective_entitlements(account.pk, start - timedelta(seconds=1))["source"]
        == "restricted"
    )
    assert get_effective_entitlements(account.pk, start)["source"] == "manual"
    assert get_effective_entitlements(account.pk, end)["source"] == "restricted"
    suspend_account(admin, account.pk, suspended=True, reason="Pause")
    assert get_effective_entitlements(account.pk, start)["source"] == "suspended"
    suspend_account(admin, account.pk, suspended=False, reason="Resume")
    assert get_effective_entitlements(account.pk, start)["source"] == "manual"


@pytest.mark.django_db
def test_grant_rejects_wrong_plan_and_capacity(data_fixture):
    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_account, create_plan
    from rest_framework.exceptions import ValidationError

    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    team = create_plan(admin, code="team", name="Team", kind="TEAM")
    personal = create_plan(admin, code="personal", name="Personal", kind="INDIVIDUAL")
    with pytest.raises(ValidationError):
        replace_grant(
            admin,
            account.pk,
            plan=team,
            seat_limit=1,
            starts_at=timezone.now(),
            reason="Wrong plan",
        )
    with pytest.raises(ValidationError):
        replace_grant(
            admin,
            account.pk,
            plan=personal,
            seat_limit=2,
            starts_at=timezone.now(),
            reason="Too many seats",
        )


@pytest.mark.django_db
def test_admin_grants_and_revokes_complimentary_team_access(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    user = data_fixture.create_user()
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    account = api_client.post(
        "/api/billing/admin/accounts/",
        {
            "kind": "TEAM",
            "responsible_user": user.id,
        },
        format="json",
    ).data
    plan = api_client.post(
        "/api/billing/admin/plans/",
        {
            "code": "team",
            "name": "Team",
            "kind": "TEAM",
        },
        format="json",
    ).data
    url = f"/api/billing/admin/accounts/{account['id']}/grant/"
    grant = api_client.put(
        url,
        {
            "plan": plan["id"],
            "seat_limit": 12,
            "starts_at": timezone.now().isoformat(),
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "reason": "Complimentary partner account",
        },
        format="json",
    )
    assert grant.status_code == 200
    assert grant.data["effective"]["source"] == "manual"
    assert grant.data["effective"]["seat_limit"] == 12
    revoked = api_client.post(
        url + "revoke/", {"reason": "Partner agreement ended"}, format="json"
    )
    assert revoked.status_code == 200
    assert revoked.data["effective"]["source"] == "restricted"
    audit = api_client.get(f"/api/billing/admin/accounts/{account['id']}/audit/")
    assert [row["action"] for row in audit.data["results"]][:2] == [
        "grant.revoked",
        "grant.updated",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "suspended,future,expected",
    [(True, False, "suspended"), (False, True, "restricted"), (False, False, "manual")],
)
def test_preview_matches_saved_access(
    api_client, data_fixture, suspended, future, expected
):
    from jadawel_billing.handlers import create_account, create_plan
    from jadawel_billing.models import ManualEntitlementGrant

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    account.suspended = suspended
    account.save()
    plan = create_plan(admin, code="preview", name="Preview", kind="INDIVIDUAL")
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    url = f"/api/billing/admin/accounts/{account.pk}/grant/"
    payload = dict(
        plan=plan.pk,
        seat_limit=1,
        starts_at=(timezone.now() + timedelta(days=1 if future else -1)).isoformat(),
        reason="Preview regression",
    )
    preview = api_client.post(url + "preview/", payload, format="json")
    assert preview.status_code == 200
    assert not ManualEntitlementGrant.objects.filter(account=account).exists()
    saved = api_client.put(url, payload, format="json")
    assert saved.status_code == 200
    assert preview.data["effective_after"]["source"] == expected
    assert preview.data["effective_after"] == saved.data["effective"]


@pytest.mark.django_db
def test_failed_renewal_keeps_access_during_configured_grace(data_fixture, settings):
    from jadawel_billing.entitlements import get_effective_entitlements
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, PaymentAttempt, Subscription

    settings.JADAWEL_BILLING_GRACE_DAYS = 7
    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind="INDIVIDUAL", responsible_user=admin)
    plan = create_plan(admin, code="grace", name="Grace", kind="INDIVIDUAL")
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    now = timezone.now()
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        amount=price.amount,
        interval=price.interval,
        mode="test",
    )
    PaymentAttempt.objects.create(order=order, given_id=order.payment_id)
    subscription = Subscription.objects.create(
        account=account,
        price=price,
        seats=1,
        period_start=now - timedelta(days=31),
        period_end=now - timedelta(days=1),
        source_order=order,
        status=Subscription.Status.GRACE,
        cancel_at_period_end=False,
    )
    assert get_effective_entitlements(account.pk, now)["source"] == "grace"
    after_grace = subscription.period_end + timedelta(days=7)
    assert get_effective_entitlements(account.pk, after_grace)["source"] == "restricted"
