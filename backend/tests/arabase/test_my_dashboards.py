"""The "My dashboards" page (لوحاتي) — docs/MY_DASHBOARDS.md.

A user collects dashboards from their own workspaces and by public link, here
or on another Jadawel server. Every read is checked when it happens: the page
never shows more than the user could open elsewhere, a link's password is asked
for again once its owner changes it, and nothing leaks between users.
"""

import json

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import reverse
from django.test import override_settings

import pytest
import responses
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_502_BAD_GATEWAY,
)

from advocate import AddrValidator, UnacceptableAddressException
from arabase.dashboard.share.handler import DashboardShareHandler
from arabase.saved_dashboards.exceptions import SavedDashboardUnreachable
from arabase.saved_dashboards.handler import PASSWORD_SEALER
from arabase.saved_dashboards.models import SavedDashboard
from arabase.saved_dashboards.remote import RemoteDashboardClient
from jadawel.contrib.database.webhooks import validators
from jadawel.core.trash.handler import TrashHandler

REMOTE = "https://other.example"
REMOTE_SLUG = "remote-slug"
REMOTE_API = f"{REMOTE}/api/arabase/public/dashboard/{REMOTE_SLUG}/"
REMOTE_LINK = f"{REMOTE}/public/dashboard/{REMOTE_SLUG}"
REMOTE_PAYLOAD = {
    "dashboard": {"id": 7, "name": "Their sales", "description": ""},
    "widgets": [{"id": 1, "type": "summary", "width": 3, "height": 2}],
    "data_sources": [{"id": 11, "type": "local_jadawel_aggregate_rows"}],
}


@pytest.fixture(autouse=True)
def clear_throttles():
    cache.clear()


def auth(token):
    return {"HTTP_AUTHORIZATION": f"JWT {token}"}


def with_token(token):
    return responses.matchers.header_matcher(
        {settings.PUBLIC_VIEW_AUTHORIZATION_HEADER: f"JWT {token}"}
    )


def protected_info(accepts):
    """The other server's info endpoint, answering only to the token given."""

    def respond(request):
        header = request.headers.get(settings.PUBLIC_VIEW_AUTHORIZATION_HEADER)
        if header == f"JWT {accepts}":
            return 200, {}, json.dumps(REMOTE_PAYLOAD)
        return 401, {}, "{}"

    return respond


def local_link(slug):
    return f"{settings.PUBLIC_WEB_FRONTEND_URL}/public/dashboard/{slug}"


def cards(api_client, token):
    response = api_client.get(reverse("api:arabase:my_dashboards"), **auth(token))
    assert response.status_code == HTTP_200_OK
    return response.json()


def add_link(api_client, token, url, password=""):
    return api_client.post(
        reverse("api:arabase:my_dashboards_add_link"),
        {"url": url, "password": password},
        format="json",
        **auth(token),
    )


def add_workspace(api_client, token, dashboard_id):
    return api_client.post(
        reverse("api:arabase:my_dashboards_add_workspace"),
        {"dashboard_id": dashboard_id},
        format="json",
        **auth(token),
    )


def content(api_client, token, saved_id):
    return api_client.get(
        reverse(
            "api:arabase:my_dashboard_content", kwargs={"saved_dashboard_id": saved_id}
        ),
        **auth(token),
    )


def dispatch(api_client, token, saved_id, data_source_id):
    return api_client.post(
        reverse(
            "api:arabase:my_dashboard_dispatch",
            kwargs={"saved_dashboard_id": saved_id, "data_source_id": data_source_id},
        ),
        **auth(token),
    )


def enter_password(api_client, token, saved_id, password):
    return api_client.post(
        reverse(
            "api:arabase:my_dashboard_password", kwargs={"saved_dashboard_id": saved_id}
        ),
        {"password": password},
        format="json",
        **auth(token),
    )


@pytest.fixture
def sales(data_fixture):
    """A workspace with a dashboard whose one widget sums a number field."""

    owner, owner_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=owner, name="Finance")
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_number_field(table=table, name="Amount")
    model = table.get_model()
    model.objects.create(**{f"field_{field.id}": 10})
    model.objects.create(**{f"field_{field.id}": 32})
    dashboard = data_fixture.create_dashboard_application(
        workspace=workspace, name="Sales"
    )
    integration = data_fixture.create_local_jadawel_integration(
        application=dashboard, user=owner
    )
    data_source = (
        data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
            dashboard=dashboard,
            integration=integration,
            table=table,
            field=field,
            aggregation_type="sum",
        )
    )
    data_fixture.create_summary_widget(
        dashboard=dashboard, data_source=data_source, title="Total"
    )
    return {
        "owner": owner,
        "owner_token": owner_token,
        "workspace": workspace,
        "dashboard": dashboard,
        "data_source": data_source,
    }


# ---------------------------------------------------------------------------
# From the user's own workspaces
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_member_adds_a_dashboard_of_their_workspace(api_client, sales):
    response = add_workspace(api_client, sales["owner_token"], sales["dashboard"].id)

    assert response.status_code == HTTP_200_OK
    card = response.json()
    assert card["source"] == "workspace"
    assert card["title"] == "Sales"
    assert card["source_name"] == "Finance"
    assert card["status"] == "ok"
    assert card["dashboard_id"] == sales["dashboard"].id
    assert card["preview"] == [{"type": "summary", "width": 12, "height": 4}]

    # Adding it again keeps the one card.
    again = add_workspace(api_client, sales["owner_token"], sales["dashboard"].id)
    assert again.json()["id"] == card["id"]
    assert [c["id"] for c in cards(api_client, sales["owner_token"])] == [card["id"]]


@pytest.mark.django_db
def test_the_page_shows_the_dashboard_with_the_members_permissions(api_client, sales):
    token = sales["owner_token"]
    saved_id = add_workspace(api_client, token, sales["dashboard"].id).json()["id"]

    body = content(api_client, token, saved_id).json()
    assert body["dashboard"]["name"] == "Sales"
    assert [d["id"] for d in body["data_sources"]] == [sales["data_source"].id]
    assert [w["title"] for w in body["widgets"]] == ["Total"]

    response = dispatch(api_client, token, saved_id, sales["data_source"].id)
    assert response.status_code == HTTP_200_OK
    assert response.json()["result"] == "42"


@pytest.mark.django_db
def test_a_data_source_of_another_dashboard_cannot_be_dispatched(
    api_client, data_fixture, sales
):
    token = sales["owner_token"]
    saved_id = add_workspace(api_client, token, sales["dashboard"].id).json()["id"]
    other = data_fixture.create_dashboard_application(workspace=sales["workspace"])
    foreign = data_fixture.create_dashboard_local_jadawel_aggregate_rows_data_source(
        dashboard=other
    )

    response = dispatch(api_client, token, saved_id, foreign.id)

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_only_dashboards_of_the_users_workspaces_can_be_added(
    api_client, data_fixture, sales
):
    _, stranger_token = data_fixture.create_user_and_token()
    response = add_workspace(api_client, stranger_token, sales["dashboard"].id)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    database = data_fixture.create_database_application(workspace=sales["workspace"])
    response = add_workspace(api_client, sales["owner_token"], database.id)
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_available_lists_the_users_dashboards_by_workspace(
    api_client, data_fixture, sales
):
    token = sales["owner_token"]
    second = data_fixture.create_dashboard_application(
        workspace=sales["workspace"], name="Costs"
    )
    data_fixture.create_dashboard_application(name="Someone else's")
    add_workspace(api_client, token, sales["dashboard"].id)

    response = api_client.get(
        reverse("api:arabase:my_dashboards_available"), **auth(token)
    )

    assert response.json() == [
        {
            "id": sales["workspace"].id,
            "name": "Finance",
            "dashboards": [
                {"id": sales["dashboard"].id, "name": "Sales", "saved": True},
                {"id": second.id, "name": "Costs", "saved": False},
            ],
        }
    ]


@pytest.mark.django_db
def test_a_member_who_leaves_the_workspace_can_no_longer_open_it(
    api_client, data_fixture, sales
):
    member, member_token = data_fixture.create_user_and_token()
    workspace_user = data_fixture.create_user_workspace(
        workspace=sales["workspace"], user=member
    )
    saved_id = add_workspace(api_client, member_token, sales["dashboard"].id).json()[
        "id"
    ]

    workspace_user.delete()

    assert cards(api_client, member_token)[0]["status"] == "unavailable"
    response = content(api_client, member_token, saved_id)
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_UNAVAILABLE"
    response = dispatch(api_client, member_token, saved_id, sales["data_source"].id)
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_UNAVAILABLE"


@pytest.mark.django_db
def test_a_trashed_dashboard_is_unavailable(api_client, sales):
    token = sales["owner_token"]
    saved_id = add_workspace(api_client, token, sales["dashboard"].id).json()["id"]

    TrashHandler.trash(
        sales["owner"], sales["workspace"], sales["dashboard"], sales["dashboard"]
    )

    assert cards(api_client, token)[0]["status"] == "unavailable"
    assert content(api_client, token, saved_id).status_code == HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# By a link on this server
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_anyone_adds_another_users_dashboard_by_its_link(
    api_client, data_fixture, sales
):
    _, token = data_fixture.create_user_and_token()
    slug = DashboardShareHandler().create_share(sales["dashboard"]).slug

    response = add_link(api_client, token, local_link(slug))

    assert response.status_code == HTTP_200_OK
    card = response.json()
    assert card["source"] == "link"
    assert card["title"] == "Sales"
    # The owner's workspace is not disclosed to a link visitor.
    assert card["source_name"] == ""
    assert card["dashboard_id"] is None

    body = content(api_client, token, card["id"]).json()
    public = api_client.get(
        reverse("api:arabase:public_dashboard", kwargs={"slug": slug})
    ).json()
    assert body == public
    response = dispatch(api_client, token, card["id"], sales["data_source"].id)
    assert response.json()["result"] == "42"


@pytest.mark.django_db
def test_the_owner_adds_their_own_dashboard_by_link(api_client, sales):
    slug = DashboardShareHandler().create_share(sales["dashboard"]).slug

    response = add_link(api_client, sales["owner_token"], f"{local_link(slug)}/auth")

    assert response.status_code == HTTP_200_OK
    assert response.json()["title"] == "Sales"


@pytest.mark.django_db
def test_a_password_protected_link_needs_its_password(api_client, data_fixture, sales):
    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(sales["dashboard"]), "secret-123")
    url = local_link(share.slug)

    response = add_link(api_client, token, url)
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED"

    response = add_link(api_client, token, url, "wrong-password")
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT"
    assert not SavedDashboard.objects.exists()

    response = add_link(api_client, token, url, "secret-123")
    assert response.status_code == HTTP_200_OK
    saved = SavedDashboard.objects.get()
    # The hash it was granted under, never the password itself.
    assert saved.granted_password == share.public_view_password
    assert "secret-123" not in json.dumps(
        {f.name: str(getattr(saved, f.attname)) for f in saved._meta.fields}
    )
    assert content(api_client, token, saved.id).status_code == HTTP_200_OK


@pytest.mark.django_db
def test_access_lasts_until_the_owner_changes_the_password(
    api_client, data_fixture, sales
):
    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(sales["dashboard"]), "secret-123")
    saved_id = add_link(api_client, token, local_link(share.slug), "secret-123").json()[
        "id"
    ]

    handler.set_password(share, "new-secret-456")

    assert cards(api_client, token)[0]["status"] == "password"
    response = content(api_client, token, saved_id)
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED"
    response = dispatch(api_client, token, saved_id, sales["data_source"].id)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    assert enter_password(api_client, token, saved_id, "secret-123").status_code == (
        HTTP_401_UNAUTHORIZED
    )
    response = enter_password(api_client, token, saved_id, "new-secret-456")
    assert response.status_code == HTTP_200_OK
    assert response.json()["status"] == "ok"
    assert content(api_client, token, saved_id).status_code == HTTP_200_OK


@pytest.mark.django_db
def test_adding_a_password_to_an_open_link_asks_for_it(api_client, data_fixture, sales):
    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.create_share(sales["dashboard"])
    add_link(api_client, token, local_link(share.slug))

    handler.set_password(share, "secret-123")

    assert cards(api_client, token)[0]["status"] == "password"


@pytest.mark.django_db
def test_a_rotated_or_revoked_link_is_unavailable(api_client, data_fixture, sales):
    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.create_share(sales["dashboard"])
    saved_id = add_link(api_client, token, local_link(share.slug)).json()["id"]

    handler.rotate_slug(share)
    assert cards(api_client, token)[0]["status"] == "unavailable"
    assert content(api_client, token, saved_id).json()["error"] == (
        "ERROR_SAVED_DASHBOARD_UNAVAILABLE"
    )

    handler.delete_share(sales["dashboard"])
    assert cards(api_client, token)[0]["status"] == "unavailable"


@pytest.mark.django_db
def test_links_that_are_not_dashboard_links_are_refused(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    for url in (
        "not a link",
        f"{settings.PUBLIC_WEB_FRONTEND_URL}/database/1/table/2",
        "ftp://other.example/public/dashboard/abc",
        # Another server's password must not travel over plain http.
        "http://other.example/public/dashboard/abc",
    ):
        response = add_link(api_client, token, url)
        assert response.status_code == HTTP_400_BAD_REQUEST, url
        assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_LINK_INVALID"

    response = add_link(api_client, token, local_link("does-not-exist"))
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_UNAVAILABLE"


@pytest.mark.django_db
def test_password_guesses_are_throttled_like_the_public_prompt(
    api_client, data_fixture, sales
):
    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(sales["dashboard"]), "secret-123")
    url = local_link(share.slug)

    for _ in range(10):
        assert add_link(api_client, token, url, "guess").status_code == (
            HTTP_401_UNAUTHORIZED
        )
    assert add_link(api_client, token, url, "secret-123").status_code == (
        HTTP_429_TOO_MANY_REQUESTS
    )


@pytest.mark.django_db
def test_rewriting_the_link_does_not_reset_the_throttle(
    api_client, data_fixture, sales
):
    """The link's path is all that is read, so a query string or the `/auth`
    page must count against the same link."""

    _, token = data_fixture.create_user_and_token()
    handler = DashboardShareHandler()
    share = handler.set_password(handler.create_share(sales["dashboard"]), "secret-123")
    url = local_link(share.slug)

    for attempt in range(10):
        variant = f"{url}/auth" if attempt % 2 else f"{url}?attempt={attempt}"
        assert add_link(api_client, token, variant, "guess").status_code == (
            HTTP_401_UNAUTHORIZED
        )
    assert add_link(api_client, token, f"{url}?fresh=1", "secret-123").status_code == (
        HTTP_429_TOO_MANY_REQUESTS
    )


# ---------------------------------------------------------------------------
# By a link on another Jadawel server
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@responses.activate
def test_a_dashboard_on_another_server_is_read_through_this_one(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token()
    responses.get(REMOTE_API, json=REMOTE_PAYLOAD)
    responses.post(f"{REMOTE_API}dispatch/11/", json={"result": 5})

    response = add_link(api_client, token, REMOTE_LINK)

    assert response.status_code == HTTP_200_OK
    card = response.json()
    assert card["source"] == "remote"
    assert card["title"] == "Their sales"
    assert card["source_name"] == "other.example"
    assert card["preview"] == [{"type": "summary", "width": 3, "height": 2}]
    assert content(api_client, token, card["id"]).json() == REMOTE_PAYLOAD
    assert dispatch(api_client, token, card["id"], 11).json() == {"result": 5}


@pytest.mark.django_db
@responses.activate
def test_a_remote_password_is_kept_sealed_and_renews_the_token(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token()
    responses.add_callback(
        responses.GET, REMOTE_API, callback=protected_info(accepts="first")
    )
    responses.post(f"{REMOTE_API}auth/", json={"access_token": "first"})

    response = add_link(api_client, token, REMOTE_LINK)
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED"

    response = add_link(api_client, token, REMOTE_LINK, "remote-secret")
    assert response.status_code == HTTP_200_OK
    saved = SavedDashboard.objects.get()
    assert saved.remote_token == "first"
    assert "remote-secret" not in saved.password_sealed
    assert PASSWORD_SEALER.unseal(saved.password_sealed) == "remote-secret"

    # The other server expired the token: the sealed password gets a new one,
    # without asking the user.
    responses.post(
        f"{REMOTE_API}dispatch/11/",
        status=401,
        json={},
        match=[with_token("first")],
    )
    responses.post(
        f"{REMOTE_API}auth/",
        json={"access_token": "second"},
        match=[responses.matchers.json_params_matcher({"password": "remote-secret"})],
    )
    responses.post(
        f"{REMOTE_API}dispatch/11/", json={"result": 1}, match=[with_token("second")]
    )

    response = dispatch(api_client, token, saved.id, 11)

    assert response.status_code == HTTP_200_OK
    assert response.json() == {"result": 1}
    saved.refresh_from_db()
    assert saved.remote_token == "second"


@pytest.mark.django_db
@responses.activate
def test_a_changed_remote_password_asks_the_user_again(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    saved = SavedDashboard.objects.create(
        user=user,
        source="remote",
        origin=REMOTE,
        slug=REMOTE_SLUG,
        password_sealed=PASSWORD_SEALER.seal("old-secret"),
        remote_token="expired",
    )
    responses.get(REMOTE_API, status=401, json={})
    responses.post(f"{REMOTE_API}auth/", status=401, json={})

    response = content(api_client, token, saved.id)

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED"
    assert cards(api_client, token)[0]["status"] == "password"

    responses.reset()
    responses.post(f"{REMOTE_API}auth/", json={"access_token": "fresh"})
    responses.get(REMOTE_API, json=REMOTE_PAYLOAD)
    response = enter_password(api_client, token, saved.id, "new-secret")
    assert response.status_code == HTTP_200_OK
    assert response.json()["status"] == "ok"
    saved.refresh_from_db()
    assert PASSWORD_SEALER.unseal(saved.password_sealed) == "new-secret"
    assert content(api_client, token, saved.id).status_code == HTTP_200_OK


@pytest.mark.django_db
@responses.activate
def test_an_unreachable_server_is_reported_not_crashed(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    responses.get(REMOTE_API, json=REMOTE_PAYLOAD)
    saved_id = add_link(api_client, token, REMOTE_LINK).json()["id"]

    responses.reset()
    responses.get(REMOTE_API, body=ConnectionError("down"))
    response = content(api_client, token, saved_id)
    assert response.status_code == HTTP_502_BAD_GATEWAY
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_UNREACHABLE"
    assert cards(api_client, token)[0]["status"] == "unreachable"

    responses.reset()
    responses.get(REMOTE_API, body="<html>not a dashboard</html>")
    assert content(api_client, token, saved_id).status_code == HTTP_502_BAD_GATEWAY

    responses.reset()
    responses.get(REMOTE_API, status=404, json={})
    assert content(api_client, token, saved_id).json()["error"] == (
        "ERROR_SAVED_DASHBOARD_UNAVAILABLE"
    )
    assert cards(api_client, token)[0]["status"] == "unavailable"


@pytest.mark.django_db
@override_settings(JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS=False)
def test_links_to_internal_addresses_are_never_fetched(
    api_client, data_fixture, monkeypatch
):
    """The outbound rules webhooks follow apply: a link cannot make this server
    read its own network."""

    # Skips only the discovery of this machine's own interfaces, which needs
    # `netifaces`; private, loopback and link-local ranges are still refused.
    monkeypatch.setattr(
        validators,
        "get_advocate_address_validator",
        lambda: AddrValidator(autodetect_local_addresses=False),
    )
    _, token = data_fixture.create_user_and_token()
    for host in ("127.0.0.1", "10.0.0.5", "169.254.169.254"):
        response = add_link(api_client, token, f"https://{host}/public/dashboard/abc")
        assert response.status_code == HTTP_502_BAD_GATEWAY, host
        assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_UNREACHABLE"
        # Refused by the outbound guard, not merely a closed port.
        with pytest.raises(SavedDashboardUnreachable) as refused:
            RemoteDashboardClient(f"https://{host}", "abc").info()
        assert isinstance(refused.value.__cause__, UnacceptableAddressException)
    assert not SavedDashboard.objects.exists()


# ---------------------------------------------------------------------------
# The page itself
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_saved_dashboards_are_private_to_their_user(api_client, data_fixture, sales):
    saved_id = add_workspace(
        api_client, sales["owner_token"], sales["dashboard"].id
    ).json()["id"]
    _, other_token = data_fixture.create_user_and_token()

    assert cards(api_client, other_token) == []
    for response in (
        content(api_client, other_token, saved_id),
        dispatch(api_client, other_token, saved_id, sales["data_source"].id),
        enter_password(api_client, other_token, saved_id, "x"),
        api_client.delete(
            reverse(
                "api:arabase:my_dashboard", kwargs={"saved_dashboard_id": saved_id}
            ),
            **auth(other_token),
        ),
    ):
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_DOES_NOT_EXIST"
    assert SavedDashboard.objects.filter(id=saved_id).exists()


@pytest.mark.django_db
def test_removing_and_ordering(api_client, data_fixture, sales):
    token = sales["owner_token"]
    second = data_fixture.create_dashboard_application(
        workspace=sales["workspace"], name="Costs"
    )
    first_id = add_workspace(api_client, token, sales["dashboard"].id).json()["id"]
    second_id = add_workspace(api_client, token, second.id).json()["id"]
    assert [c["id"] for c in cards(api_client, token)] == [first_id, second_id]

    response = api_client.post(
        reverse("api:arabase:my_dashboards_order"),
        {"saved_dashboard_ids": [second_id, first_id]},
        format="json",
        **auth(token),
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert [c["id"] for c in cards(api_client, token)] == [second_id, first_id]

    response = api_client.delete(
        reverse("api:arabase:my_dashboard", kwargs={"saved_dashboard_id": second_id}),
        **auth(token),
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert [c["id"] for c in cards(api_client, token)] == [first_id]
    # Only the card goes; the dashboard stays.
    second.refresh_from_db()


@pytest.mark.django_db
def test_a_workspace_dashboard_takes_no_password(api_client, sales):
    token = sales["owner_token"]
    saved_id = add_workspace(api_client, token, sales["dashboard"].id).json()["id"]

    response = enter_password(api_client, token, saved_id, "anything")

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_SAVED_DASHBOARD_HAS_NO_PASSWORD"


@pytest.mark.django_db
def test_the_page_needs_a_signed_in_user(api_client):
    response = api_client.get(reverse("api:arabase:my_dashboards"))
    assert response.status_code == HTTP_401_UNAUTHORIZED
