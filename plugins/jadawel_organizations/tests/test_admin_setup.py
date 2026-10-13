from uuid import uuid4

import pytest

SETUP_URL = "/api/organizations/admin/setup/"


def _staff_client(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token(is_staff=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")
    return admin


def _team_plan(admin, code="setup-team"):
    from jadawel_billing.handlers import create_plan

    return create_plan(admin, code=code, name="Team", kind="TEAM")


@pytest.mark.django_db
def test_setup_adds_owner_and_members_without_invitations(
    api_client, data_fixture, mailoutbox
):
    from django.contrib.auth import get_user_model

    from jadawel_billing.entitlements import get_effective_entitlements
    from jadawel_organizations.models import (
        Organization,
        OrganizationInvitation,
        OrganizationMembership,
    )

    from jadawel.core.models import WorkspaceUser

    admin = _staff_client(api_client, data_fixture)
    plan = _team_plan(admin)
    owner = data_fixture.create_user(email="owner@example.com")
    existing = data_fixture.create_user(email="existing@example.com")

    response = api_client.post(
        SETUP_URL,
        {
            "name": "Acme",
            "owner_email": "Owner@Example.com",
            "plan": plan.pk,
            "members": [
                {"email": "existing@example.com", "role": "admin"},
                {"email": "New.Person@example.com", "name": "New Person"},
            ],
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert response["Cache-Control"] == "no-store"
    organization = Organization.objects.get(pk=response.data["id"])
    assert organization.owner_id == owner.pk
    assert organization.provisioning_status == "ready"
    roles = dict(
        OrganizationMembership.objects.filter(organization=organization).values_list(
            "user__email", "role"
        )
    )
    assert roles == {
        "owner@example.com": "owner",
        "existing@example.com": "admin",
        "new.person@example.com": "member",
    }
    assert not OrganizationInvitation.objects.filter(organization=organization).exists()
    assert mailoutbox == []
    entitlement = get_effective_entitlements(organization.billing_account_id)
    assert entitlement["seat_limit"] == 3

    # Only the account created now gets a password, and it signs in at once.
    [credential] = response.data["credentials"]
    assert credential["email"] == "new.person@example.com"
    created = get_user_model().objects.get(email="new.person@example.com")
    assert created.first_name == "New Person"
    assert created.check_password(credential["password"])
    assert created.profile.email_verified is True

    workspace_id = response.data["workspace"]["id"]
    permissions = dict(
        WorkspaceUser.objects.filter(workspace_id=workspace_id).values_list(
            "user_id", "permissions"
        )
    )
    assert permissions == {
        owner.pk: "ADMIN",
        existing.pk: "ADMIN",
        created.pk: "MEMBER",
    }
    assert admin.pk not in permissions


@pytest.mark.django_db
def test_setup_creates_an_owner_account_for_an_unknown_email(api_client, data_fixture):
    from jadawel_organizations.models import Organization

    admin = _staff_client(api_client, data_fixture)
    plan = _team_plan(admin)

    response = api_client.post(
        SETUP_URL,
        {
            "name": "Fresh",
            "owner_email": "brand-new-owner@example.com",
            "plan": plan.pk,
            "seat_limit": 10,
            "create_workspace": False,
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    organization = Organization.objects.get(pk=response.data["id"])
    assert organization.owner.email == "brand-new-owner@example.com"
    assert organization.provisioning_status == "ready"
    assert response.data["pending_owner_email"] is None
    assert response.data["effective_entitlement"]["seat_limit"] == 10
    assert response.data["workspace"] is None
    assert [item["email"] for item in response.data["credentials"]] == [
        "brand-new-owner@example.com"
    ]


@pytest.mark.django_db
def test_setup_rolls_back_everything_on_a_duplicate_email(api_client, data_fixture):
    from django.contrib.auth import get_user_model

    from jadawel_organizations.models import Organization

    admin = _staff_client(api_client, data_fixture)
    plan = _team_plan(admin)
    users_before = get_user_model().objects.count()

    response = api_client.post(
        SETUP_URL,
        {
            "name": "Twice",
            "owner_email": "new-owner@example.com",
            "plan": plan.pk,
            "members": [
                {"email": "someone@example.com"},
                {"email": "SOMEONE@example.com"},
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "duplicate_email:someone@example.com" in str(response.data)
    assert not Organization.objects.exists()
    assert get_user_model().objects.count() == users_before


@pytest.mark.django_db
def test_setup_rejects_a_deactivated_account(api_client, data_fixture):
    from jadawel_organizations.models import Organization

    admin = _staff_client(api_client, data_fixture)
    plan = _team_plan(admin)
    data_fixture.create_user(email="gone@example.com", is_active=False)

    response = api_client.post(
        SETUP_URL,
        {
            "name": "Inactive",
            "owner_email": "gone@example.com",
            "plan": plan.pk,
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Organization.objects.exists()


@pytest.mark.django_db
def test_setup_requires_a_general_administrator(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    response = api_client.post(
        SETUP_URL,
        {"name": "Nope", "owner_email": user.email, "plan": 1},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_setup_replay_returns_the_same_organization_without_passwords(
    api_client, data_fixture
):
    from django.contrib.auth import get_user_model

    from jadawel_organizations.models import Organization

    admin = _staff_client(api_client, data_fixture)
    plan = _team_plan(admin)
    key = str(uuid4())
    payload = {
        "name": "Retry",
        "owner_email": "retry-owner@example.com",
        "plan": plan.pk,
        "members": [{"email": "retry-member@example.com"}],
    }

    first = api_client.post(SETUP_URL, payload, format="json", HTTP_IDEMPOTENCY_KEY=key)
    second = api_client.post(
        SETUP_URL, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.data["id"] == first.data["id"]
    assert second.data["workspace"] == first.data["workspace"]
    assert len(first.data["credentials"]) == 2
    assert second.data["credentials"] == []
    assert Organization.objects.count() == 1
    assert (
        get_user_model()
        .objects.filter(
            email__in=["retry-owner@example.com", "retry-member@example.com"]
        )
        .count()
        == 2
    )
