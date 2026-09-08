from datetime import timedelta

import pytest
from django.utils import timezone


def test_organizations_api_has_a_stable_namespace():
    from django.urls import reverse

    assert reverse("api:jadawel_organizations:list") == "/api/organizations/"


@pytest.mark.django_db
def test_general_admin_creates_complimentary_organization(data_fixture):
    from jadawel_billing.models import BillingAccount
    from jadawel_organizations.handlers import create_organization
    from jadawel_organizations.models import OrganizationMembership

    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(admin, name="Acme", owner=owner)
    assert organization.billing_account.kind == BillingAccount.Kind.TEAM
    assert (
        OrganizationMembership.objects.get(organization=organization, user=owner).role
        == "owner"
    )


@pytest.mark.django_db
def test_invitation_acceptance_enforces_seats_and_email(data_fixture):
    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import (
        accept_invitation,
        create_organization,
        invite_member,
    )
    from jadawel_organizations.models import OrganizationMembership
    from rest_framework.exceptions import PermissionDenied, ValidationError

    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user(email="owner@example.com")
    member = data_fixture.create_user(email="member@example.com")
    other = data_fixture.create_user(email="other@example.com")
    organization = create_organization(admin, name="Acme", owner=owner)
    plan = create_plan(admin, code="team", name="Team", kind="TEAM")
    replace_grant(
        admin,
        organization.billing_account_id,
        plan=plan,
        seat_limit=2,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Complimentary launch access",
    )
    invitation, token = invite_member(owner, organization, email=member.email)
    with pytest.raises(PermissionDenied):
        accept_invitation(other, token)
    accept_invitation(member, token)
    assert OrganizationMembership.objects.filter(organization=organization).count() == 2
    invitation2, token2 = invite_member(owner, organization, email=other.email)
    with pytest.raises(ValidationError):
        accept_invitation(other, token2)
    invitation2.refresh_from_db()
    assert invitation2.accepted_at is None


@pytest.mark.django_db
def test_workspace_binding_syncs_and_removes_managed_access(data_fixture):
    from jadawel.core.models import WorkspaceUser
    from jadawel_organizations.handlers import (
        assign_workspace_member,
        bind_workspace,
        create_organization,
        remove_member,
    )
    from jadawel_organizations.models import OrganizationMembership

    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    member = data_fixture.create_user()
    organization = create_organization(admin, name="Acme", owner=owner)
    member_membership = OrganizationMembership.objects.create(
        organization=organization, user=member
    )
    workspace = data_fixture.create_workspace(user=owner, name="Acme data")
    bind_workspace(admin, organization, workspace)
    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()
    assert not WorkspaceUser.objects.filter(workspace=workspace, user=member).exists()
    assign_workspace_member(
        owner, organization, organization.workspaces.get(), member_membership
    )
    assert WorkspaceUser.objects.filter(workspace=workspace, user=member).exists()
    remove_member(admin, organization, member_membership)
    assert not WorkspaceUser.objects.filter(workspace=workspace, user=member).exists()
    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()


@pytest.mark.django_db
def test_workspace_binding_restores_preexisting_access_on_member_removal(data_fixture):
    from jadawel.core.models import WorkspaceUser
    from jadawel_organizations.handlers import (
        assign_workspace_member,
        bind_workspace,
        create_organization,
        remove_member,
    )
    from jadawel_organizations.models import OrganizationMembership

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    member = data_fixture.create_user()
    organization = create_organization(staff, name="Preserve access", owner=owner)
    membership = OrganizationMembership.objects.create(
        organization=organization, user=member
    )
    workspace = data_fixture.create_workspace(user=owner, name="Shared data")
    preexisting = WorkspaceUser.objects.create(
        workspace=workspace, user=member, order=1, permissions="ADMIN"
    )
    bind_workspace(staff, organization, workspace)
    assign_workspace_member(
        owner, organization, organization.workspaces.get(), membership
    )
    preexisting.refresh_from_db()
    assert preexisting.permissions == "MEMBER"
    remove_member(owner, organization, membership)
    preexisting.refresh_from_db()
    assert preexisting.permissions == "ADMIN"


@pytest.mark.django_db
def test_organization_suspend_preserves_preexisting_workspace_membership(data_fixture):
    from jadawel.core.models import WorkspaceUser
    from jadawel_organizations.handlers import (
        assign_workspace_member,
        bind_workspace,
        change_organization_lifecycle,
        create_organization,
        unbind_workspace,
    )
    from jadawel_organizations.models import OrganizationMembership

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    member = data_fixture.create_user()
    organization = create_organization(staff, name="Preserve suspension", owner=owner)
    membership = OrganizationMembership.objects.create(
        organization=organization, user=member
    )
    workspace = data_fixture.create_workspace(user=owner, name="Preserved shared data")
    preexisting = WorkspaceUser.objects.create(
        workspace=workspace, user=member, order=1, permissions="ADMIN"
    )
    bind_workspace(staff, organization, workspace)
    binding = organization.workspaces.get()
    assign_workspace_member(owner, organization, binding, membership)

    change_organization_lifecycle(staff, organization, action="suspend")
    assert WorkspaceUser.objects.filter(pk=preexisting.pk).exists()
    change_organization_lifecycle(staff, organization, action="reactivate")
    unbind_workspace(staff, organization, binding)
    preexisting.refresh_from_db()
    assert preexisting.permissions == "ADMIN"


@pytest.mark.django_db
def test_managed_workspace_uses_organization_permission_and_restricted_mode(
    data_fixture,
):
    from django.utils import timezone
    from jadawel.core.exceptions import PermissionException
    from jadawel.core.handler import CoreHandler
    from jadawel_billing.grants import replace_grant, revoke_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import bind_workspace, create_organization

    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(admin, name="Secure", owner=owner)
    plan = create_plan(admin, code="secure-team", name="Secure Team", kind="TEAM")
    replace_grant(
        admin,
        organization.billing_account_id,
        plan=plan,
        seat_limit=2,
        starts_at=timezone.now(),
        reason="Access",
    )
    workspace = data_fixture.create_workspace(user=owner, name="Managed")
    bind_workspace(owner, organization, workspace)
    assert CoreHandler().check_permissions(
        owner, "workspace.read", workspace=workspace, context=workspace
    )
    revoke_grant(admin, organization.billing_account_id, reason="Restriction test")
    with pytest.raises(PermissionException):
        CoreHandler().check_permissions(
            owner,
            "workspace.create_application",
            workspace=workspace,
            context=workspace,
        )
    with pytest.raises(PermissionException):
        CoreHandler().check_permissions(
            owner,
            "workspace.mark_notification_as_read",
            workspace=workspace,
            context=workspace,
        )
    token = data_fixture.create_token(user=owner, workspace=workspace)
    assert CoreHandler().check_permissions(
        owner,
        "workspace.token.use",
        workspace=workspace,
        context=token,
    )


@pytest.mark.django_db
def test_viewer_workspace_assignment_is_read_only(data_fixture):
    from django.utils import timezone
    from jadawel.core.exceptions import PermissionException
    from jadawel.core.handler import CoreHandler
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
    organization = create_organization(staff, name="Viewer access", owner=owner)
    plan = create_plan(staff, code="viewer-team", name="Viewer team", kind="TEAM")
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=2,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Viewer assignment",
    )
    membership = OrganizationMembership.objects.create(
        organization=organization, user=viewer
    )
    workspace = data_fixture.create_workspace(user=owner, name="Viewer data")
    bind_workspace(owner, organization, workspace)
    assign_workspace_member(
        owner,
        organization,
        organization.workspaces.get(),
        membership,
        permissions="VIEWER",
    )
    assert CoreHandler().check_permissions(
        viewer, "workspace.read", workspace=workspace, context=workspace
    )
    with pytest.raises(PermissionException):
        CoreHandler().check_permissions(
            viewer,
            "workspace.create_application",
            workspace=workspace,
            context=workspace,
        )


@pytest.mark.django_db
def test_staff_without_explicit_organization_access_cannot_read_managed_workspace(
    data_fixture,
):
    from django.utils import timezone
    from jadawel.core.exceptions import PermissionException
    from jadawel.core.handler import CoreHandler
    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import bind_workspace, create_organization

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(staff, name="Explicit staff access", owner=owner)
    plan = create_plan(
        staff, code="explicit-staff-access", name="Explicit staff access", kind="TEAM"
    )
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=1,
        starts_at=timezone.now(),
        reason="Access boundary",
    )
    workspace = data_fixture.create_workspace(user=owner, name="Managed staff boundary")
    bind_workspace(owner, organization, workspace)

    with pytest.raises(PermissionException):
        CoreHandler().check_permissions(
            staff, "workspace.read", workspace=workspace, context=workspace
        )


@pytest.mark.django_db
def test_owner_cannot_bind_workspace_they_do_not_administer(data_fixture):
    from django.utils import timezone
    from rest_framework.exceptions import PermissionDenied
    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import bind_workspace, create_organization

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    other_owner = data_fixture.create_user()
    organization = create_organization(staff, name="Workspace boundary", owner=owner)
    plan = create_plan(
        staff, code="workspace-boundary", name="Workspace boundary", kind="TEAM"
    )
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=1,
        starts_at=timezone.now(),
        reason="Workspace boundary",
    )
    workspace = data_fixture.create_workspace(user=other_owner, name="Other workspace")

    with pytest.raises(PermissionDenied, match="workspace_admin_required"):
        bind_workspace(owner, organization, workspace)


@pytest.mark.django_db
def test_paid_team_settlement_provisions_organization_once(data_fixture, settings):
    from unittest.mock import Mock, patch
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.models import BillingOrder, PaymentAttempt
    from jadawel_billing.payments import reconcile_order_system
    from jadawel_organizations.models import Organization, OrganizationMembership

    settings.JADAWEL_MOYASAR_SECRET_KEY = "sk_test_fixture"
    settings.JADAWEL_BILLING_MODE = "test"
    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    account = create_account(admin, kind="TEAM", responsible_user=owner)
    plan = create_plan(admin, code="paid-team", name="Paid Team", kind="TEAM")
    price = create_price(admin, plan=plan, amount=5000, interval="MONTH")
    order = BillingOrder.objects.create(
        account=account,
        price=price,
        seats=3,
        amount=5000,
        interval="MONTH",
        mode="test",
    )
    attempt = PaymentAttempt.objects.create(
        order=order,
        given_id=order.payment_id,
        provider_mode="test",
        provider_payment_id="paid-team-payment",
    )
    response = Mock(status_code=200)
    response.json.return_value = {
        "id": "paid-team-payment",
        "status": "paid",
        "amount": 5000,
        "currency": "SAR",
        "metadata": {"billing_order": str(order.pk)},
    }
    with patch("requests.get", return_value=response):
        reconcile_order_system(order, provider_payment_id=attempt.provider_payment_id)
        reconcile_order_system(order, provider_payment_id=attempt.provider_payment_id)
    organization = Organization.objects.get(billing_account=account)
    assert organization.provisioning_status == "ready"
    assert OrganizationMembership.objects.filter(
        organization=organization, user=owner, role="owner"
    ).exists()


@pytest.mark.django_db
def test_admin_organization_api_and_invitation_api(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token(is_staff=True)
    owner = data_fixture.create_user(email="api-owner@example.com")
    member = data_fixture.create_user(email="api-member@example.com")
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    response = api_client.post(
        "/api/organizations/admin/create/",
        {"name": "API Team", "owner": owner.pk},
        format="json",
    )
    assert response.status_code == 201
    organization_id = response.data["id"]
    invitation = api_client.post(
        f"/api/organizations/{organization_id}/invitations/",
        {"email": member.email, "role": "member"},
        format="json",
    )
    assert invitation.status_code == 201
    assert invitation.data["token"]
    api_client.credentials()
    denied = api_client.get(f"/api/organizations/{organization_id}/")
    assert denied.status_code == 401


@pytest.mark.django_db
def test_organization_owner_can_update_name_with_audit_entry(data_fixture):
    from jadawel_organizations.handlers import create_organization, update_organization
    from jadawel_organizations.models import OrganizationAuditEvent

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(staff, name="Before name", owner=owner)

    updated = update_organization(owner, organization, name="After name")

    assert updated.name == "After name"
    event = OrganizationAuditEvent.objects.get(
        organization=organization, action="organization.updated"
    )
    assert event.details == {
        "before": {"name": "Before name"},
        "after": {"name": "After name"},
    }


@pytest.mark.django_db
def test_general_admin_can_create_complimentary_org_with_grant(
    api_client, data_fixture
):
    from jadawel_billing.models import ManualEntitlementGrant
    from jadawel_billing.handlers import create_plan

    admin, token = data_fixture.create_user_and_token(is_staff=True)
    owner = data_fixture.create_user(email="grant-owner@example.com")
    plan = create_plan(admin, code="admin-grant-team", name="Admin Team", kind="TEAM")
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    response = api_client.post(
        "/api/organizations/admin/create/",
        {
            "name": "Complimentary Team",
            "owner": owner.pk,
            "plan": plan.pk,
            "seat_limit": 5,
            "reason": "Launch support",
        },
        format="json",
    )
    assert response.status_code == 201
    assert ManualEntitlementGrant.objects.filter(
        account_id=response.data["billing_account"], seat_limit=5
    ).exists()


@pytest.mark.django_db
def test_admin_owner_email_creates_reserved_setup_invitation(data_fixture):
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import accept_invitation, create_organization
    from jadawel_organizations.models import Organization, OrganizationMembership

    admin = data_fixture.create_user(is_staff=True)
    plan = create_plan(admin, code="pending-owner", name="Pending owner", kind="TEAM")
    organization = create_organization(
        admin,
        name="Pending owner team",
        owner_email="new-owner@example.com",
        plan=plan,
        seat_limit=2,
        reason="Onboarding access",
    )
    assert organization.owner_id is None
    assert organization.provisioning_status == Organization.ProvisioningStatus.PENDING
    assert organization.invitations.filter(role="owner").count() == 1
    from jadawel_organizations.handlers import team_occupied_seats

    assert team_occupied_seats(organization.billing_account_id) == 1
    workspace = data_fixture.create_workspace(user=admin, name="Pending owner data")
    from jadawel_organizations.handlers import bind_workspace
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError, match="outsiders_require_confirmation"):
        bind_workspace(admin, organization, workspace)
    bind_workspace(admin, organization, workspace, confirm_outsiders=True)
    owner = data_fixture.create_user(email="new-owner@example.com")
    accept_invitation(owner, organization._owner_setup_token)
    organization.refresh_from_db()
    assert organization.owner_id == owner.pk
    assert organization.provisioning_status == Organization.ProvisioningStatus.READY
    assert (
        OrganizationMembership.objects.get(organization=organization, user=owner).role
        == "owner"
    )
    from jadawel.core.models import WorkspaceUser

    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()


@pytest.mark.django_db
def test_restricted_team_cannot_create_new_workspace(data_fixture):
    from django.utils import timezone
    from jadawel.core.exceptions import PermissionException
    from jadawel.core.handler import CoreHandler
    from jadawel_billing.grants import replace_grant, revoke_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import create_organization

    admin = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(admin, name="Restricted", owner=owner)
    plan = create_plan(admin, code="restricted-team", name="Restricted", kind="TEAM")
    replace_grant(
        admin,
        organization.billing_account_id,
        plan=plan,
        seat_limit=1,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Temporary access",
    )
    revoke_grant(admin, organization.billing_account_id, reason="Expired access")
    with pytest.raises(PermissionException):
        CoreHandler().create_workspace(owner, name="Should be blocked")


@pytest.mark.django_db
def test_public_workspace_policy_preserves_records_but_hides_restricted_links(
    data_fixture,
):
    from django.utils import timezone
    from jadawel_billing.grants import replace_grant, revoke_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import bind_workspace, create_organization
    from jadawel_organizations.policy import public_workspace_allowed

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(staff, name="Public policy", owner=owner)
    plan = create_plan(staff, code="public-policy", name="Public policy", kind="TEAM")
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=1,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Public link test",
    )
    workspace = data_fixture.create_workspace(user=owner, name="Shared")
    bind_workspace(owner, organization, workspace)
    assert public_workspace_allowed(workspace)
    from arabase.dashboard.share.handler import DashboardShareHandler
    from arabase.dashboard.share.exceptions import DashboardShareDoesNotExist

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    share = DashboardShareHandler().create_share(dashboard)
    assert DashboardShareHandler().get_share_by_slug(share.slug) == share
    revoke_grant(staff, organization.billing_account_id, reason="Restricted")
    assert not public_workspace_allowed(workspace)
    with pytest.raises(DashboardShareDoesNotExist):
        DashboardShareHandler().get_share_by_slug(share.slug)


@pytest.mark.django_db
def test_existing_user_add_and_role_authority(data_fixture):
    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import (
        add_member,
        create_organization,
        update_member,
    )
    from rest_framework.exceptions import PermissionDenied

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    manager = data_fixture.create_user()
    member = data_fixture.create_user()
    organization = create_organization(staff, name="Role team", owner=owner)
    plan = create_plan(staff, code="role-team", name="Role team", kind="TEAM")
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=3,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Role test",
    )
    manager_membership = add_member(owner, organization, user=manager, role="admin")
    with pytest.raises(PermissionDenied):
        add_member(manager, organization, user=member, role="admin")
    member_membership = add_member(owner, organization, user=member)
    with pytest.raises(PermissionDenied):
        update_member(manager, organization, member_membership, role="admin")
    update_member(owner, organization, manager_membership, role="member")


@pytest.mark.django_db
def test_lifecycle_revokes_and_restores_managed_workspace_access(data_fixture):
    from jadawel.core.models import WorkspaceUser
    from jadawel_organizations.handlers import (
        bind_workspace,
        change_organization_lifecycle,
        create_organization,
    )

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    organization = create_organization(staff, name="Lifecycle", owner=owner)
    workspace = data_fixture.create_workspace(user=owner, name="Lifecycle data")
    bind_workspace(owner, organization, workspace)
    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()
    change_organization_lifecycle(staff, organization, action="suspend")
    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()
    from jadawel.core.exceptions import PermissionException
    from jadawel.core.handler import CoreHandler

    with pytest.raises(PermissionException):
        CoreHandler().check_permissions(
            owner, "workspace.read", workspace=workspace, context=workspace
        )
    change_organization_lifecycle(staff, organization, action="reactivate")
    assert WorkspaceUser.objects.filter(workspace=workspace, user=owner).exists()


@pytest.mark.django_db
def test_suspended_member_keeps_team_seat_reserved(data_fixture):
    from django.utils import timezone
    from rest_framework.exceptions import ValidationError

    from jadawel_billing.grants import replace_grant
    from jadawel_billing.handlers import create_plan
    from jadawel_organizations.handlers import (
        add_member,
        create_organization,
        update_member,
    )

    staff = data_fixture.create_user(is_staff=True)
    owner = data_fixture.create_user()
    member = data_fixture.create_user()
    replacement = data_fixture.create_user()
    organization = create_organization(staff, name="Reserved seats", owner=owner)
    plan = create_plan(staff, code="reserved-seats", name="Reserved seats", kind="TEAM")
    replace_grant(
        staff,
        organization.billing_account_id,
        plan=plan,
        seat_limit=2,
        starts_at=timezone.now() - timedelta(minutes=1),
        reason="Seat reservation test",
    )
    membership = add_member(owner, organization, user=member)
    update_member(owner, organization, membership, suspended=True)
    update_member(owner, organization, membership, suspended=False)
    update_member(owner, organization, membership, suspended=True)
    with pytest.raises(ValidationError):
        add_member(owner, organization, user=replacement)


@pytest.mark.django_db
def test_team_order_quote_is_per_purchased_seat(data_fixture):
    from jadawel_billing.handlers import create_account, create_plan, create_price
    from jadawel_billing.payments import create_order

    staff = data_fixture.create_user(is_staff=True)
    payer = data_fixture.create_user()
    account = create_account(staff, kind="TEAM", responsible_user=payer)
    plan = create_plan(
        staff, code="per-seat", name="Per seat", kind="TEAM", available=True
    )
    price = create_price(
        staff, plan=plan, amount=5000, interval="MONTH", available=True
    )
    order = create_order(payer, account, price, 3)
    assert order.amount == 15000
