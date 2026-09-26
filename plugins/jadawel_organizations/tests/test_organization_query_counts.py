"""Characterization and query-count tests for the organizations hotspots.

The characterization tests pin the permission outcomes and admin rows from
before the per-call caches, so the caching change proves it returns the same
results. The query-count tests pin the counts the caches achieve.
"""

from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

import pytest

MIXED_OPERATIONS = [
    "workspace.read",
    "workspace.update",
    "workspace.create_invitation",
    "database.table.read",
    "application.update",
]
ADMIN_LIST_URL = "/api/organizations/admin/"


def _manager():
    from jadawel.core.registries import permission_manager_type_registry

    return permission_manager_type_registry.get("organization")


def _checks(actor, operations=MIXED_OPERATIONS):
    from jadawel.core.types import PermissionCheck

    return [PermissionCheck(actor, operation) for operation in operations]


def _outcomes(result):
    """Reduce a result to comparable values: True or (exception type, args)."""

    return {
        check: True if value is True else (type(value), value.args)
        for check, value in result.items()
    }


def _summary(result):
    return {
        (check.actor.pk, check.operation_name): (True if value is True else type(value))
        for check, value in result.items()
    }


def _batch_matching_single_checks(checks, workspace=None):
    """Run the checks as one batch and assert each single check agrees."""

    manager = _manager()
    batch = manager.check_multiple_permissions(checks, workspace)
    singles = {}
    for check in checks:
        singles.update(manager.check_multiple_permissions([check], workspace))
    assert _outcomes(batch) == _outcomes(singles)
    return batch


def _managed_workspace(data_fixture, *, entitled=True):
    """An organization whose owner has ADMIN and a member VIEWER access."""

    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import (
        assign_workspace_member,
        bind_workspace,
        create_organization,
    )
    from jadawel_organizations.models import OrganizationMembership

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    viewer = data_fixture.create_user()
    organization = create_organization(staff, name="Query counts", owner=owner)
    if entitled:
        plan = create_plan(staff, code="query-team", name="Query team", kind="TEAM")
        replace_grant(
            staff,
            organization.billing_account_id,
            plan=plan,
            seat_limit=5,
            starts_at=timezone.now() - timedelta(minutes=1),
            reason="Query counts",
        )
    membership = OrganizationMembership.objects.create(
        organization=organization, user=viewer
    )
    workspace = data_fixture.create_workspace(user=owner, name="Managed counts")
    bind_workspace(owner, organization, workspace)
    assign_workspace_member(
        owner,
        organization,
        organization.workspaces.get(),
        membership,
        permissions="VIEWER",
    )
    return staff, owner, viewer, organization, workspace


# (c) OrganizationPermissionManagerType.check_multiple_permissions.


@pytest.mark.django_db
def test_bound_workspace_batch_matches_single_checks_for_a_viewer(data_fixture):
    from jadawel.core.exceptions import PermissionDenied

    _, _, viewer, _, workspace = _managed_workspace(data_fixture)

    result = _batch_matching_single_checks(_checks(viewer), workspace)

    # Reads are absent (no opinion); writes and legacy membership mutations deny.
    assert _summary(result) == {
        (viewer.pk, "workspace.update"): PermissionDenied,
        (viewer.pk, "workspace.create_invitation"): PermissionDenied,
        (viewer.pk, "application.update"): PermissionDenied,
    }


@pytest.mark.django_db
def test_bound_workspace_batch_with_mixed_actors_matches_single_checks(
    data_fixture,
):
    from jadawel.core.exceptions import PermissionDenied, UserNotInWorkspace

    staff, owner, viewer, _, workspace = _managed_workspace(data_fixture)
    outsider = data_fixture.create_user()
    token = data_fixture.create_token(user=viewer, workspace=workspace)
    checks = (
        _checks(owner)
        + _checks(viewer)
        + _checks(outsider)
        + _checks(staff)
        + _checks(token, ["workspace.read", "workspace.update"])
    )

    result = _batch_matching_single_checks(checks, workspace)

    # A token is judged as its user: the viewer's token gets the viewer's result.
    expected = {}
    for check in checks:
        if check.actor is outsider or check.actor is staff:
            expected[check] = UserNotInWorkspace
        elif check.operation_name == "workspace.create_invitation":
            expected[check] = PermissionDenied
        elif check.actor is not owner and check.operation_name in {
            "workspace.update",
            "application.update",
        }:
            expected[check] = PermissionDenied
    assert {check: type(value) for check, value in result.items()} == expected


@pytest.mark.django_db
def test_bound_workspace_branch_order(data_fixture):
    """Pin the if/elif order: access, legacy mutation, restriction, viewer."""

    from jadawel_billing.grants import suspend_account
    from jadawel_organizations.handlers import change_organization_lifecycle

    from jadawel.core.exceptions import PermissionDenied, UserNotInWorkspace

    staff, owner, viewer, organization, workspace = _managed_workspace(
        data_fixture, entitled=False
    )
    outsider = data_fixture.create_user()

    # Access comes first: a non-member and staff without an access row get
    # UserNotInWorkspace for every operation, legacy mutations included.
    for actor in (outsider, staff):
        result = _batch_matching_single_checks(_checks(actor), workspace)
        assert _summary(result) == {
            (actor.pk, operation): UserNotInWorkspace for operation in MIXED_OPERATIONS
        }

    # Restricted (no grant, no subscription): reads pass, writes deny.
    result = _batch_matching_single_checks(_checks(owner), workspace)
    assert _summary(result) == {
        (owner.pk, "workspace.update"): PermissionDenied,
        (owner.pk, "workspace.create_invitation"): PermissionDenied,
        (owner.pk, "application.update"): PermissionDenied,
    }

    # A suspended billing account denies reads as well.
    suspend_account(
        staff, organization.billing_account_id, suspended=True, reason="Pause"
    )
    for actor in (owner, viewer):
        result = _batch_matching_single_checks(_checks(actor), workspace)
        assert _summary(result) == {
            (actor.pk, operation): PermissionDenied for operation in MIXED_OPERATIONS
        }
    result = _batch_matching_single_checks(_checks(outsider), workspace)
    assert _summary(result) == {
        (outsider.pk, operation): UserNotInWorkspace for operation in MIXED_OPERATIONS
    }

    # A suspended organization drops every access row out of the lookup.
    suspend_account(
        staff, organization.billing_account_id, suspended=False, reason="Resume"
    )
    change_organization_lifecycle(staff, organization, action="suspend")
    result = _batch_matching_single_checks(_checks(owner), workspace)
    assert _summary(result) == {
        (owner.pk, operation): UserNotInWorkspace for operation in MIXED_OPERATIONS
    }


@pytest.mark.django_db
def test_unbound_workspace_has_no_organization_opinion(data_fixture):
    owner = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=owner, name="Personal")

    assert _batch_matching_single_checks(_checks(owner), workspace) == {}


@pytest.mark.django_db
def test_global_checks_allow_staff_and_block_restricted_workspace_creation(
    data_fixture,
):
    from jadawel.core.exceptions import PermissionDenied

    staff, owner, viewer, _, _ = _managed_workspace(data_fixture, entitled=False)
    entitled_owner = _managed_workspace(data_fixture, entitled=True)[1]
    operations = ["create_workspace", "workspace.read", "workspace.update"]

    staff_result = _batch_matching_single_checks(_checks(staff, operations))
    assert _summary(staff_result) == {
        (staff.pk, operation): True for operation in operations
    }
    for actor in (owner, viewer):
        result = _batch_matching_single_checks(_checks(actor, operations))
        assert _summary(result) == {(actor.pk, "create_workspace"): PermissionDenied}
    assert _batch_matching_single_checks(_checks(entitled_owner, operations)) == {}

    mixed = _checks(staff, operations) + _checks(owner, operations)
    result = _batch_matching_single_checks(mixed)
    assert _summary(result) == {
        **{(staff.pk, operation): True for operation in operations},
        (owner.pk, "create_workspace"): PermissionDenied,
    }


@pytest.mark.django_db
def test_global_checks_query_count_ignores_non_creation_operations(data_fixture):
    _, owner, _, _, _ = _managed_workspace(data_fixture, entitled=False)
    manager = _manager()
    one = _checks(owner, ["create_workspace"])
    five = _checks(owner, ["create_workspace"] + MIXED_OPERATIONS[:4])
    manager.check_multiple_permissions(one, None)

    with CaptureQueriesContext(connection) as single:
        manager.check_multiple_permissions(one, None)
    with CaptureQueriesContext(connection) as batch:
        manager.check_multiple_permissions(five, None)

    assert len(batch) == len(single)


@pytest.mark.django_db
def test_bound_workspace_query_count_does_not_grow_with_checks(data_fixture):
    _, _, viewer, _, workspace = _managed_workspace(data_fixture)
    manager = _manager()
    checks = _checks(viewer)
    manager.check_multiple_permissions(checks[:1], workspace)

    with CaptureQueriesContext(connection) as single:
        manager.check_multiple_permissions(checks[:1], workspace)
    with CaptureQueriesContext(connection) as batch:
        manager.check_multiple_permissions(checks, workspace)

    # Before the per-call cache: 4 queries for K=1 and 8 for K=5 (one access
    # lookup per check). Now the access row is read once per user.
    assert len(batch) == len(single)


@pytest.mark.django_db
def test_global_checks_query_count_does_not_grow_with_creation_checks(
    data_fixture,
):
    from jadawel.core.types import PermissionCheck

    _, owner, _, _, _ = _managed_workspace(data_fixture, entitled=False)
    manager = _manager()
    # Five distinct checks for the same user, told apart only by their context.
    checks = [
        PermissionCheck(owner, "create_workspace", context)
        for context in ("a", "b", "c", "d", "e")
    ]
    manager.check_multiple_permissions(checks[:1], None)

    with CaptureQueriesContext(connection) as single:
        single_result = manager.check_multiple_permissions(checks[:1], None)
    with CaptureQueriesContext(connection) as batch:
        batch_result = manager.check_multiple_permissions(checks, None)

    assert len(single_result) == 1
    assert len(batch_result) == 5
    # Before the per-call cache: 4 queries for K=1 and 20 for K=5 (organizations
    # plus entitlements for every check). Now they are read once per user.
    assert len(batch) == len(single)


# (d) The organizations admin list.


def _paid_pending_organization(data_fixture, staff, index, now):
    from jadawel_billing.handlers import create_plan, create_price
    from jadawel_billing.models import BillingOrder, Subscription
    from jadawel_organizations.handlers import create_organization

    organization = create_organization(
        staff,
        name=f"Paid pending {index}",
        owner_email=f"pending-owner-{index}@example.com",
    )
    plan = create_plan(
        staff, code=f"paid-pending-{index}", name=f"Paid {index}", kind="TEAM"
    )
    price = create_price(staff, plan=plan, amount=5000, interval="MONTH")
    order = BillingOrder.objects.create(
        account_id=organization.billing_account_id,
        price=price,
        seats=3 + index,
        amount=price.amount,
        interval=price.interval,
        mode="test",
        status="paid",
    )
    subscription = Subscription.objects.create(
        account_id=organization.billing_account_id,
        price=price,
        seats=3 + index,
        period_start=now - timedelta(days=1),
        period_end=now + timedelta(days=29),
        source_order=order,
        cancel_at_period_end=False,
    )
    return organization, subscription


def _list_organizations(api_client):
    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(ADMIN_LIST_URL)
    assert response.status_code == 200
    return response, len(queries)


@pytest.mark.django_db
def test_admin_organization_row_snapshot(api_client, data_fixture):
    from jadawel_organizations.models import OrganizationMembership
    from rest_framework.fields import DateTimeField

    staff, token = data_fixture.create_user_and_token(is_staff=True)
    now = timezone.now()
    organization, subscription = _paid_pending_organization(data_fixture, staff, 0, now)
    OrganizationMembership.objects.create(
        organization=organization, user=data_fixture.create_user()
    )
    OrganizationMembership.objects.create(
        organization=organization, user=data_fixture.create_user(), suspended=True
    )
    for index in (1, 2):
        _paid_pending_organization(data_fixture, staff, index, now)
    organization.refresh_from_db()
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    response, _ = _list_organizations(api_client)

    rows = {row["id"]: row for row in response.json()["results"]}
    assert len(rows) == 3
    datetime_field = DateTimeField()
    # owner_email is absent, not null, while the owner is still pending.
    assert rows[str(organization.pk)] == {
        "id": str(organization.pk),
        "name": "Paid pending 0",
        "status": "active",
        "provisioning_status": "pending",
        "owner": None,
        "pending_owner_email": "pending-owner-0@example.com",
        "billing_account": str(organization.billing_account_id),
        "members_count": 1,
        "effective_source": "paid",
        "effective_seat_limit": 3,
        "subscription_status": "active",
        "subscription_period_end": datetime_field.to_representation(
            subscription.period_end
        ),
        "subscription_cancel_at_period_end": False,
        "created_at": datetime_field.to_representation(organization.created_at),
    }
    assert list(rows[str(organization.pk)]) == [
        "id",
        "name",
        "status",
        "provisioning_status",
        "owner",
        "pending_owner_email",
        "billing_account",
        "members_count",
        "effective_source",
        "effective_seat_limit",
        "subscription_status",
        "subscription_period_end",
        "subscription_cancel_at_period_end",
        "created_at",
    ]


@pytest.mark.django_db
def test_admin_organization_list_per_row_query_delta(api_client, data_fixture):
    staff, token = data_fixture.create_user_and_token(is_staff=True)
    now = timezone.now()
    _paid_pending_organization(data_fixture, staff, 0, now)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    _list_organizations(api_client)

    _, one_organization = _list_organizations(api_client)
    for index in (1, 2):
        _paid_pending_organization(data_fixture, staff, index, now)
    response, three_organizations = _list_organizations(api_client)

    assert len(response.json()["results"]) == 3
    per_row = (three_organizations - one_organization) / 2
    # Per paid row this was D = 12: two get_effective_entitlements calls of 4
    # queries each (account, grant, subscription, price), three subscription
    # reads and one pending-owner invitation read. With entitlements at 3
    # queries and _effective/_subscription memoised per organization it is 5.
    assert per_row <= 5
