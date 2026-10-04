"""Who may use automations, applications and Sanad (docs/FEATURE_ACCESS.md).

Staff always may. An administrator opens each feature to every user, or grants
it to email addresses; the login response tells the frontend which to show, and
the server refuses creating an automation or an application, or using Sanad,
to anyone else.
"""

import json
from unittest.mock import patch

from django.shortcuts import reverse
from django.test import override_settings

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from arabase.feature_access.exceptions import FeatureNotGranted
from arabase.feature_access.handler import (
    add_grants,
    get_user_features,
    has_feature,
    remove_grant,
    set_everyone,
)
from arabase.feature_access.models import FeatureAccess, FeatureAccessGrant
from arabase.sanad.models import SanadChat
from jadawel.core.handler import CoreHandler
from jadawel.core.jobs.models import Job

LIST_URL = "api:arabase:admin_feature_access"
NOTHING = {"automation": False, "builder": False, "sanad": False}
EVERYTHING = {"automation": True, "builder": True, "sanad": True}


def auth(token):
    return {"HTTP_AUTHORIZATION": f"JWT {token}"}


def feature_url(feature):
    return reverse("api:arabase:admin_feature", kwargs={"feature": feature})


def grants_url(feature):
    return reverse("api:arabase:admin_feature_grants", kwargs={"feature": feature})


def grant_url(feature, grant_id):
    return reverse(
        "api:arabase:admin_feature_grant",
        kwargs={"feature": feature, "grant_id": grant_id},
    )


def by_feature(response):
    return {item["feature"]: item for item in response.json()["features"]}


@pytest.fixture
def admin(data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    return {"user": user, "headers": auth(token)}


def create_app(api_client, token, workspace, type_name):
    return api_client.post(
        reverse("api:applications:list", kwargs={"workspace_id": workspace.id}),
        {"name": "New", "type": type_name},
        format="json",
        **auth(token),
    )


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_staff_has_every_feature_and_others_none_by_default(data_fixture):
    staff = data_fixture.create_user(is_staff=True)
    member = data_fixture.create_user()

    assert get_user_features(staff) == EVERYTHING
    assert get_user_features(member) == NOTHING
    assert get_user_features(None) == NOTHING


@pytest.mark.django_db
def test_opening_a_feature_to_everyone(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    member = data_fixture.create_user()

    set_everyone(admin, "automation", True)

    assert get_user_features(member) == {**NOTHING, "automation": True}
    assert has_feature(member, "automation")
    assert FeatureAccess.objects.get(feature="automation").updated_by == admin

    set_everyone(admin, "automation", False)
    assert not has_feature(member, "automation")


@pytest.mark.django_db
def test_a_grant_follows_the_email_address_in_any_case(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    member = data_fixture.create_user(email="Mixed.Case@Example.com")
    other = data_fixture.create_user()

    assert add_grants(admin, "builder", [" mixed.case@EXAMPLE.com "]) == [
        "mixed.case@example.com"
    ]

    assert get_user_features(member) == {**NOTHING, "builder": True}
    assert not has_feature(other, "builder")


@pytest.mark.django_db
def test_a_grant_for_an_address_without_an_account_covers_it_later(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    add_grants(admin, "sanad", ["newcomer@example.com"])

    newcomer = data_fixture.create_user(email="newcomer@example.com")

    assert has_feature(newcomer, "sanad")


@pytest.mark.django_db
def test_granting_twice_keeps_one_grant(data_fixture):
    admin = data_fixture.create_user(is_staff=True)

    assert add_grants(admin, "sanad", ["a@example.com", "A@example.com"]) == [
        "a@example.com"
    ]
    assert add_grants(admin, "sanad", ["a@example.com", "b@example.com"]) == [
        "b@example.com"
    ]
    assert FeatureAccessGrant.objects.filter(feature="sanad").count() == 2


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_only_administrators_reach_the_settings(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=False)
    grant = FeatureAccessGrant.objects.create(feature="sanad", email="x@example.com")

    assert api_client.get(reverse(LIST_URL)).status_code == HTTP_401_UNAUTHORIZED
    requests = [
        lambda: api_client.get(reverse(LIST_URL), **auth(token)),
        lambda: api_client.patch(
            feature_url("sanad"), {"everyone": True}, format="json", **auth(token)
        ),
        lambda: api_client.post(
            grants_url("sanad"),
            {"emails": ["y@example.com"]},
            format="json",
            **auth(token),
        ),
        lambda: api_client.delete(grant_url("sanad", grant.id), **auth(token)),
    ]
    for request in requests:
        assert request().status_code == HTTP_403_FORBIDDEN

    assert not FeatureAccess.objects.exists()
    assert list(FeatureAccessGrant.objects.values_list("email", flat=True)) == [
        "x@example.com"
    ]


@pytest.mark.django_db
def test_the_listing_starts_limited_to_staff(api_client, admin):
    response = api_client.get(reverse(LIST_URL), **admin["headers"])

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "features": [
            {"feature": "automation", "everyone": False, "grants": []},
            {"feature": "builder", "everyone": False, "grants": []},
            {"feature": "sanad", "everyone": False, "grants": []},
        ]
    }


@pytest.mark.django_db
def test_administrator_opens_and_grants_features(api_client, admin, data_fixture):
    member = data_fixture.create_user(email="member@example.com", first_name="Mona")

    response = api_client.patch(
        feature_url("automation"), {"everyone": True}, format="json", **admin["headers"]
    )
    assert response.status_code == HTTP_200_OK
    assert by_feature(response)["automation"]["everyone"] is True

    response = api_client.post(
        grants_url("sanad"),
        {"emails": ["Member@Example.com", "invitee@example.com"]},
        format="json",
        **admin["headers"],
    )
    assert response.status_code == HTTP_200_OK
    grants = by_feature(response)["sanad"]["grants"]
    assert [grant["email"] for grant in grants] == [
        "invitee@example.com",
        "member@example.com",
    ]
    assert grants[0]["user"] is None
    assert grants[1]["user"] == {
        "id": member.id,
        "name": "Mona",
        "is_staff": False,
        "is_active": True,
    }
    assert by_feature(response)["builder"]["grants"] == []

    response = api_client.delete(
        grant_url("sanad", grants[1]["id"]), **admin["headers"]
    )
    assert response.status_code == HTTP_200_OK
    assert [g["email"] for g in by_feature(response)["sanad"]["grants"]] == [
        "invitee@example.com"
    ]


@pytest.mark.django_db
def test_invalid_requests_are_refused(api_client, admin):
    grant = FeatureAccessGrant.objects.create(feature="sanad", email="x@example.com")

    response = api_client.patch(
        feature_url("dashboard"), {"everyone": True}, format="json", **admin["headers"]
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FEATURE_DOES_NOT_EXIST"

    response = api_client.post(
        grants_url("sanad"),
        {"emails": ["not an email"]},
        format="json",
        **admin["headers"],
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = api_client.post(
        grants_url("sanad"), {"emails": []}, format="json", **admin["headers"]
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    response = api_client.patch(
        feature_url("sanad"), {}, format="json", **admin["headers"]
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    # A grant is removed through its own feature only.
    response = api_client.delete(grant_url("builder", grant.id), **admin["headers"])
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_FEATURE_GRANT_DOES_NOT_EXIST"
    assert FeatureAccessGrant.objects.filter(id=grant.id).exists()


# ---------------------------------------------------------------------------
# What the user receives
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_login_response_carries_the_users_features(api_client, data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    data_fixture.create_user(email="member@example.com", password="password")
    add_grants(admin, "builder", ["member@example.com"])

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "member@example.com", "password": "password"},
        format="json",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["arabase_features"] == {**NOTHING, "builder": True}

    refreshed = api_client.post(
        reverse("api:user:token_refresh"),
        {"refresh_token": response.json()["refresh_token"]},
        format="json",
    )
    assert refreshed.json()["arabase_features"] == {**NOTHING, "builder": True}


@pytest.mark.django_db(transaction=True)
def test_signed_in_users_are_told_of_changes(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    granted = data_fixture.create_user(email="granted@example.com")
    other = data_fixture.create_user()

    def message(feature, value):
        return {
            "type": "user_data_updated",
            "user_data": {"arabase_features": {feature: value}},
        }

    with patch("jadawel.ws.tasks.broadcast_to_users.delay") as broadcast:
        add_grants(admin, "sanad", ["granted@example.com"])
    broadcast.assert_called_once_with(
        [granted.id], message("sanad", True), send_to_all_users=False
    )

    with patch("jadawel.ws.tasks.broadcast_to_users.delay") as broadcast:
        set_everyone(admin, "sanad", True)
    broadcast.assert_called_once_with(
        [], message("sanad", True), send_to_all_users=True
    )

    # Closing it again only takes it from users with neither staff nor a grant.
    with patch("jadawel.ws.tasks.broadcast_to_users.delay") as broadcast:
        set_everyone(admin, "sanad", False)
    broadcast.assert_called_once_with(
        [other.id], message("sanad", False), send_to_all_users=False
    )

    with patch("jadawel.ws.tasks.broadcast_to_users.delay") as broadcast:
        set_everyone(admin, "sanad", False)
    broadcast.assert_not_called()

    grant = FeatureAccessGrant.objects.get(email="granted@example.com")
    with patch("jadawel.ws.tasks.broadcast_to_users.delay") as broadcast:
        remove_grant("sanad", grant.id)
    broadcast.assert_called_once_with(
        [granted.id], message("sanad", False), send_to_all_users=False
    )


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_creating_automations_and_applications_needs_the_feature(
    api_client, data_fixture
):
    admin = data_fixture.create_user(is_staff=True)
    user, token = data_fixture.create_user_and_token(email="member@example.com")
    workspace = data_fixture.create_workspace(user=user)

    for type_name in ("automation", "builder"):
        response = create_app(api_client, token, workspace, type_name)
        assert response.status_code == HTTP_403_FORBIDDEN, type_name
        assert response.json()["error"] == "ERROR_FEATURE_DISABLED"
    assert create_app(api_client, token, workspace, "database").status_code == (
        HTTP_200_OK
    )

    add_grants(admin, "builder", ["member@example.com"])
    set_everyone(admin, "automation", True)

    for type_name in ("automation", "builder"):
        response = create_app(api_client, token, workspace, type_name)
        assert response.status_code == HTTP_200_OK, response.json()


@pytest.mark.django_db(transaction=True)
@patch("jadawel.core.jobs.handler.run_async_job")
def test_installing_a_template_needs_the_features_it_creates(
    run_async_job, api_client, data_fixture, tmp_path
):
    """A template with an automation is refused like creating one is; the
    check runs before the job is queued, so the user gets the 403 at once."""

    admin = data_fixture.create_user(is_staff=True)
    user, token = data_fixture.create_user_and_token(email="member@example.com")
    workspace = data_fixture.create_workspace(user=user)
    for slug, types in (
        ("with-automation", ["database", "automation"]),
        ("databases-only", ["database"]),
    ):
        (tmp_path / f"{slug}.json").write_text(
            json.dumps({"export": [{"type": t, "name": t} for t in types]})
        )
    automation_template = data_fixture.create_template(slug="with-automation")
    database_template = data_fixture.create_template(slug="databases-only")

    def install(template):
        return api_client.post(
            reverse(
                "api:templates:install_async",
                kwargs={"workspace_id": workspace.id, "template_id": template.id},
            ),
            **auth(token),
        )

    with override_settings(APPLICATION_TEMPLATES_DIR=str(tmp_path)):
        response = install(automation_template)
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json()["error"] == "ERROR_FEATURE_DISABLED"
        run_async_job.delay.assert_not_called()

        assert install(database_template).status_code == HTTP_202_ACCEPTED
        # One install job at a time per user; the mocked one never finishes.
        Job.objects.update(state="finished")

        add_grants(admin, "automation", ["member@example.com"])
        assert install(automation_template).status_code == HTTP_202_ACCEPTED


@pytest.mark.django_db
def test_staff_create_both_without_any_setting(data_fixture):
    staff = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=staff)

    for type_name in ("automation", "builder"):
        CoreHandler().create_application(staff, workspace, type_name, name="A")


@pytest.mark.django_db
def test_sanad_tools_cannot_create_a_feature_the_user_lacks(data_fixture):
    """Sanad creates automations and applications through the same handler,
    so opening Sanad alone does not open the other two."""

    from jadawel.core.action.registries import action_type_registry
    from jadawel.core.actions import CreateApplicationActionType

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    with pytest.raises(FeatureNotGranted):
        action_type_registry.get_by_type(CreateApplicationActionType).do(
            user, workspace, "automation", name="A"
        )


@pytest.mark.django_db
def test_existing_applications_stay_with_the_workspace(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(workspace=workspace)

    response = api_client.get(
        reverse("api:applications:item", kwargs={"application_id": automation.id}),
        **auth(token),
    )

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_sanad_follows_the_setting(api_client, data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user, token = data_fixture.create_user_and_token(email="member@example.com")
    workspace = data_fixture.create_workspace(user=user)
    url = reverse("api:arabase:sanad_chats", kwargs={"workspace_id": workspace.id})

    assert api_client.post(url, **auth(token)).status_code == HTTP_403_FORBIDDEN

    add_grants(admin, "sanad", ["member@example.com"])
    response = api_client.post(url, **auth(token))
    assert response.status_code == HTTP_200_OK, response.json()
    assert SanadChat.objects.filter(user=user).count() == 1

    remove_grant("sanad", FeatureAccessGrant.objects.get(feature="sanad").id)
    response = api_client.get(url, **auth(token))
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json()["error"] == "ERROR_SANAD_NOT_ALLOWED"


@pytest.mark.django_db
def test_sanad_budget_stays_with_staff(api_client, data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user, token = data_fixture.create_user_and_token(email="member@example.com")
    workspace = data_fixture.create_workspace(user=user)
    set_everyone(admin, "sanad", True)
    url = reverse("api:arabase:sanad_budget", kwargs={"workspace_id": workspace.id})

    assert api_client.get(url, **auth(token)).status_code == HTTP_200_OK
    response = api_client.put(
        url,
        {"monthly_turn_limit": 1000, "monthly_token_limit": None},
        format="json",
        **auth(token),
    )
    assert response.status_code == HTTP_403_FORBIDDEN
