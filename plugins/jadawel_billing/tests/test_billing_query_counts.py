"""Characterization and query-count tests for the billing hotspots.

The characterization tests pin the payloads, so the batching changes
(``select_related`` on the accounts list and on the paid subscription) are
proven to return the same rows. The query-count tests pin the batched counts.
"""

from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

import pytest

ADMIN_ACCOUNTS_URL = "/api/billing/admin/accounts/"


def _list_accounts(api_client):
    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(ADMIN_ACCOUNTS_URL)
    assert response.status_code == 200
    return response, len(queries)


def _account_with_active_subscription(data_fixture, kind, now):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, Subscription

    admin = data_fixture.create_user(is_staff=True)
    account = create_account(admin, kind=kind, responsible_user=admin)
    plan = create_plan(
        admin, code=f"paid-{kind.lower()}", name=f"Paid {kind}", kind=kind
    )
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    seats = 1 if kind == "INDIVIDUAL" else 4
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        seats=seats,
        amount=price.amount,
        interval=price.interval,
        mode="test",
        status="paid",
    )
    subscription = Subscription.objects.create(
        account=account,
        price=price,
        seats=seats,
        period_start=now - timedelta(days=1),
        period_end=now + timedelta(days=29),
        source_order=order,
        cancel_at_period_end=False,
    )
    return account, plan, subscription


# (a) Billing admin accounts list.


@pytest.mark.django_db
def test_admin_accounts_rows_keep_their_keys_order_and_owner_email(
    api_client, data_fixture
):
    from jadawel_billing.handlers import create_account

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    owners = [
        data_fixture.create_user(email=f"accounts-owner-{index}@example.com")
        for index in range(3)
    ]
    accounts = [
        create_account(admin, kind="TEAM", responsible_user=owner) for owner in owners
    ]
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    response, _ = _list_accounts(api_client)

    rows = response.json()["results"]
    assert len(rows) == 3
    # The queryset orders by ("-created_at", "id"): the newest account comes first.
    assert [row["id"] for row in rows] == [str(a.pk) for a in reversed(accounts)]
    for row, account, owner in zip(rows, reversed(accounts), reversed(owners)):
        assert list(row) == [
            "id",
            "kind",
            "responsible_user",
            "owner_email",
            "created_at",
        ]
        assert row["kind"] == "TEAM"
        assert row["responsible_user"] == owner.pk
        assert row["owner_email"] == owner.email
        assert row["id"] == str(account.pk)


@pytest.mark.django_db
def test_admin_accounts_query_count_does_not_grow_with_rows(api_client, data_fixture):
    from jadawel_billing.handlers import create_account

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    create_account(admin, kind="TEAM", responsible_user=data_fixture.create_user())
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    # Warm any per-process caches so both measured requests start equal.
    _list_accounts(api_client)

    _, one_account = _list_accounts(api_client)
    for _ in range(2):
        create_account(admin, kind="TEAM", responsible_user=data_fixture.create_user())
    response, three_accounts = _list_accounts(api_client)

    assert len(response.json()["results"]) == 3
    # responsible_user is joined, so extra rows add no lazy user queries.
    assert three_accounts == one_account


# (b) Billing get_effective_entitlements on the paid path.


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind,capabilities",
    [
        ("INDIVIDUAL", ["data_write"]),
        ("TEAM", ["data_write", "organization"]),
    ],
)
def test_paid_entitlements_return_the_exact_paid_dict(data_fixture, kind, capabilities):
    from jadawel_billing.entitlements import get_effective_entitlements

    now = timezone.now()
    account, plan, subscription = _account_with_active_subscription(
        data_fixture, kind, now
    )

    result = get_effective_entitlements(account.pk, now)

    assert list(result) == [
        "source",
        "plan",
        "seat_limit",
        "capabilities",
        "valid_until",
        "revision",
        "restriction_reason",
    ]
    assert result == {
        "source": "paid",
        "plan": plan.pk,
        "seat_limit": subscription.seats,
        "capabilities": capabilities,
        "valid_until": subscription.period_end,
        "revision": 0,
        "restriction_reason": None,
    }


@pytest.mark.django_db
def test_paid_entitlements_use_three_queries(data_fixture):
    from jadawel_billing.entitlements import get_effective_entitlements

    now = timezone.now()
    account, _, _ = _account_with_active_subscription(data_fixture, "TEAM", now)

    with CaptureQueriesContext(connection) as queries:
        result = get_effective_entitlements(account.pk, now)

    assert result["source"] == "paid"
    # Account, grant, and the subscription joined with its price.
    assert len(queries) == 3
