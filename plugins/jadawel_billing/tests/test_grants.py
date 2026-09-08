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
