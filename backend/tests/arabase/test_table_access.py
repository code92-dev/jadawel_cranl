"""Table-scoped guest access (docs/TABLE_LEVEL_ACCESS_PLAN.md).

The promise under test is narrow and absolute: a GUEST member reaches the
tables they were granted and nothing else in the workspace — not a second
table, not the database listing, not the rows of a table they were never
given, and not the schema of the table they were.
"""

from django.shortcuts import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST
from arabase.table_access.handler import TableAccessHandler
from arabase.table_access.models import PendingTableGrant, TableAccessLevel, TableGrant
from jadawel.core.handler import CoreHandler
from jadawel.core.models import WorkspaceInvitation, WorkspaceUser


def access_url(workspace):
    return reverse("api:arabase:table_access", kwargs={"workspace_id": workspace.id})


def guest_url(workspace, workspace_user):
    return reverse(
        "api:arabase:table_access_guest",
        kwargs={
            "workspace_id": workspace.id,
            "workspace_user_id": workspace_user.id,
        },
    )


def make_guest(data_fixture, workspace, table, level=TableAccessLevel.VIEWER):
    """A signed-in guest holding exactly one grant."""

    guest, token = data_fixture.create_user_and_token()
    workspace_user = data_fixture.create_user_workspace(
        workspace=workspace, user=guest, permissions=WORKSPACE_USER_PERMISSION_GUEST
    )
    TableGrant.objects.create(workspace_user=workspace_user, table=table, level=level)
    return guest, token, workspace_user


# -- the guest's own surface ------------------------------------------------


@pytest.mark.django_db
def test_guest_sees_only_the_granted_table_in_the_sidebar(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    other_database = data_fixture.create_database_application(workspace=workspace)
    granted = data_fixture.create_database_table(database=database)
    data_fixture.create_database_table(database=database)
    data_fixture.create_database_table(database=other_database)

    _, token, _ = make_guest(data_fixture, workspace, granted)

    response = api_client.get(
        reverse("api:applications:list"), HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    applications = response.json()
    assert [application["id"] for application in applications] == [database.id]
    assert [table["id"] for table in applications[0]["tables"]] == [granted.id]


@pytest.mark.django_db
def test_guest_can_read_rows_of_the_granted_table(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    _, token, _ = make_guest(data_fixture, workspace, table)

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_guest_cannot_read_rows_of_another_table(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    granted = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=secret, name="Name", primary=True)

    _, token, _ = make_guest(data_fixture, workspace, granted)

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": secret.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_a_viewer_guest_cannot_write_rows(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    _, token, _ = make_guest(data_fixture, workspace, table)

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_an_editor_guest_can_write_rows_but_not_fields(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    _, token, _ = make_guest(
        data_fixture, workspace, table, level=TableAccessLevel.EDITOR
    )

    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Smuggled", "type": "text"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_guest_cannot_create_a_table_or_an_application(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    _, token, _ = make_guest(data_fixture, workspace, table)

    response = api_client.post(
        reverse("api:database:tables:list", kwargs={"database_id": database.id}),
        {"name": "Smuggled"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = api_client.post(
        reverse("api:applications:list", kwargs={"workspace_id": workspace.id}),
        {"name": "Smuggled", "type": "database"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_a_guest_without_grants_sees_nothing(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=database)

    guest, token = data_fixture.create_user_and_token()
    data_fixture.create_user_workspace(
        workspace=workspace, user=guest, permissions=WORKSPACE_USER_PERMISSION_GUEST
    )

    response = api_client.get(
        reverse("api:applications:list"), HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == []


@pytest.mark.django_db
def test_a_normal_member_is_untouched_by_the_manager(api_client, data_fixture):
    member, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=member)
    database = data_fixture.create_database_application(workspace=workspace)
    first = data_fixture.create_database_table(database=database)
    second = data_fixture.create_database_table(database=database)

    response = api_client.get(
        reverse("api:applications:list"), HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    tables = response.json()[0]["tables"]
    assert {table["id"] for table in tables} == {first.id, second.id}


# -- the admin API ----------------------------------------------------------


@pytest.mark.django_db
def test_admin_invites_a_guest_and_the_grants_are_pending(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    response = api_client.post(
        access_url(workspace),
        {
            "email": "guest@example.com",
            "tables": [{"table_id": table.id, "level": "EDITOR"}],
            "base_url": "http://localhost:3000/workspace-invitation",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    body = response.json()
    assert body["email"] == "guest@example.com"
    assert body["tables"] == [
        {
            "table_id": table.id,
            "name": table.name,
            "database_id": database.id,
            "level": "EDITOR",
        }
    ]

    invitation = WorkspaceInvitation.objects.get(id=body["id"])
    assert invitation.permissions == WORKSPACE_USER_PERMISSION_GUEST
    assert PendingTableGrant.objects.filter(invitation=invitation).count() == 1


@pytest.mark.django_db
def test_accepting_the_invitation_materialises_the_grants(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    invited = data_fixture.create_user(email="guest@example.com")

    invitation = TableAccessHandler().invite_guest(
        user=admin,
        workspace=workspace,
        email="guest@example.com",
        tables=[{"table_id": table.id, "level": TableAccessLevel.EDITOR}],
        base_url="http://localhost:3000/workspace-invitation",
    )

    workspace_user = CoreHandler().accept_workspace_invitation(invited, invitation)

    assert workspace_user.permissions == WORKSPACE_USER_PERMISSION_GUEST
    grants = TableGrant.objects.filter(workspace_user=workspace_user)
    assert [(grant.table_id, grant.level) for grant in grants] == [
        (table.id, TableAccessLevel.EDITOR)
    ]
    # Core deletes the invitation, which must take the pending rows with it.
    assert not PendingTableGrant.objects.exists()


@pytest.mark.django_db
def test_a_table_outside_the_workspace_is_refused(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    other_workspace = data_fixture.create_workspace(user=admin)
    foreign_table = data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=other_workspace)
    )

    response = api_client.post(
        access_url(workspace),
        {
            "email": "guest@example.com",
            "tables": [{"table_id": foreign_table.id, "level": "VIEWER"}],
            "base_url": "http://localhost:3000/workspace-invitation",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_TABLE_NOT_IN_WORKSPACE"
    assert not WorkspaceInvitation.objects.exists()


@pytest.mark.django_db
def test_a_member_cannot_invite_guests(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    table = data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=workspace)
    )
    member, token = data_fixture.create_user_and_token()
    data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )

    response = api_client.post(
        access_url(workspace),
        {
            "email": "guest@example.com",
            "tables": [{"table_id": table.id, "level": "VIEWER"}],
            "base_url": "http://localhost:3000/workspace-invitation",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"


@pytest.mark.django_db
def test_admin_lists_guests_and_their_tables(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    guest, _, workspace_user = make_guest(data_fixture, workspace, table)

    response = api_client.get(access_url(workspace), HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_200_OK
    body = response.json()
    assert len(body["guests"]) == 1
    assert body["guests"][0]["email"] == guest.email
    assert body["guests"][0]["tables"][0]["table_id"] == table.id
    assert body["invitations"] == []


@pytest.mark.django_db
def test_revoking_a_grant_takes_effect_immediately(api_client, data_fixture):
    admin, admin_token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)
    _, guest_token, workspace_user = make_guest(data_fixture, workspace, table)

    rows_url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    assert (
        api_client.get(rows_url, HTTP_AUTHORIZATION=f"JWT {guest_token}").status_code
        == HTTP_200_OK
    )

    response = api_client.patch(
        guest_url(workspace, workspace_user),
        {"tables": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["tables"] == []

    assert (
        api_client.get(rows_url, HTTP_AUTHORIZATION=f"JWT {guest_token}").status_code
        == HTTP_401_UNAUTHORIZED
    )


@pytest.mark.django_db
def test_deleting_a_guest_removes_the_membership(api_client, data_fixture):
    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    table = data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=workspace)
    )
    guest, _, workspace_user = make_guest(data_fixture, workspace, table)

    response = api_client.delete(
        guest_url(workspace, workspace_user), HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert not WorkspaceUser.objects.filter(id=workspace_user.id).exists()
    assert not TableGrant.objects.filter(workspace_user_id=workspace_user.id).exists()


@pytest.mark.django_db
def test_a_normal_member_is_not_deletable_through_the_guest_endpoint(
    api_client, data_fixture
):
    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    member = data_fixture.create_user()
    workspace_user = data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )

    response = api_client.delete(
        guest_url(workspace, workspace_user), HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert WorkspaceUser.objects.filter(id=workspace_user.id).exists()


# -- linked fields ----------------------------------------------------------


@pytest.mark.django_db
def test_a_link_field_to_an_ungranted_table_is_hidden(api_client, data_fixture):
    """The grant is only as tight as the fields inside it.

    A link row field carries the primary-field values of rows in the table it
    points at, so leaving it in the payload would hand the guest data from a
    table nobody granted them.
    """

    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    granted = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=granted, name="Name", primary=True)
    data_fixture.create_text_field(table=secret, name="Name", primary=True)
    link = data_fixture.create_link_row_field(
        table=granted, link_row_table=secret, name="Secret link"
    )

    _, token, _ = make_guest(data_fixture, workspace, granted)

    response = api_client.get(
        reverse("api:database:fields:list", kwargs={"table_id": granted.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert link.id not in [field["id"] for field in response.json()]

    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": granted.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    for row in response.json()["results"]:
        assert f"field_{link.id}" not in row


@pytest.mark.django_db
def test_a_link_field_to_a_granted_table_stays_visible(api_client, data_fixture):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    first = data_fixture.create_database_table(database=database)
    second = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=first, name="Name", primary=True)
    data_fixture.create_text_field(table=second, name="Name", primary=True)
    link = data_fixture.create_link_row_field(
        table=first, link_row_table=second, name="Related"
    )

    guest, token = data_fixture.create_user_and_token()
    workspace_user = data_fixture.create_user_workspace(
        workspace=workspace, user=guest, permissions=WORKSPACE_USER_PERMISSION_GUEST
    )
    TableGrant.objects.create(workspace_user=workspace_user, table=first)
    TableGrant.objects.create(workspace_user=workspace_user, table=second)

    response = api_client.get(
        reverse("api:database:fields:list", kwargs={"table_id": first.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert link.id in [field["id"] for field in response.json()]


@pytest.mark.django_db
def test_a_normal_member_still_sees_every_field(api_client, data_fixture):
    member, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=member)
    database = data_fixture.create_database_application(workspace=workspace)
    first = data_fixture.create_database_table(database=database)
    second = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=first, name="Name", primary=True)
    data_fixture.create_text_field(table=second, name="Name", primary=True)
    link = data_fixture.create_link_row_field(
        table=first, link_row_table=second, name="Related"
    )

    response = api_client.get(
        reverse("api:database:fields:list", kwargs={"table_id": first.id}),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert link.id in [field["id"] for field in response.json()]


@pytest.mark.django_db
def test_an_organization_workspace_refuses_guest_invitations(
    api_client, data_fixture, monkeypatch
):
    """Managed workspaces keep membership inside the organizations plugin.

    The refusal is core's: `create_workspace_invitation` asks every plugin to
    validate the mutation first, so a guest invitation is rejected before any
    grant is written.
    """

    from jadawel.core.exceptions import PermissionDenied
    from jadawel.core.registries import plugin_registry

    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    table = data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=workspace)
    )

    plugin = plugin_registry.get("arabase")

    def refuse(actor, target_workspace, operation, target_user=None):
        raise PermissionDenied(actor)

    monkeypatch.setattr(
        plugin, "validate_workspace_membership_mutation", refuse, raising=False
    )

    response = api_client.post(
        access_url(workspace),
        {
            "email": "guest@example.com",
            "tables": [{"table_id": table.id, "level": "VIEWER"}],
            "base_url": "http://localhost:3000/workspace-invitation",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert not PendingTableGrant.objects.exists()
