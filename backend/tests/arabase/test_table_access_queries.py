"""Query cost of table-scoped guest access (arabase.permissions.table_grants).

The guest manager answers every permission check, and the hidden-field hook
runs for every field listing and row payload. These tests pin the answers
first and then two costs: a batch of checks must not repeat the same lookup
once per check, and the hook must reuse the role and grants a permission check
already cached for the request.

The admin API (arabase.api.table_access) is pinned the same way: the exact
bytes of every guest and invitation payload, and an invitation whose cost does
not grow with the number of tables it grants.
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest
from rest_framework.renderers import JSONRenderer
from rest_framework.status import HTTP_200_OK

from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST
from arabase.table_access.handler import TableAccessHandler
from arabase.table_access.hidden_fields import hidden_field_ids_for_guest
from arabase.table_access.models import TableAccessLevel, TableGrant
from jadawel.contrib.database.fields.handler import FieldHandler
from jadawel.contrib.database.fields.operations import ListFieldsOperationType
from jadawel.contrib.database.models import Table
from jadawel.contrib.database.operations import ListTablesDatabaseTableOperationType
from jadawel.core.cache import local_cache
from jadawel.core.exceptions import UserInvalidWorkspacePermissionsError
from jadawel.core.handler import CoreHandler
from jadawel.core.models import WorkspaceInvitation, WorkspaceUser
from jadawel.core.operations import ReadApplicationOperationType
from jadawel.core.registries import permission_manager_type_registry
from jadawel.core.types import PermissionCheck


def make_guest(data_fixture, workspace, *tables):
    guest = data_fixture.create_user()
    workspace_user = data_fixture.create_user_workspace(
        workspace=workspace, user=guest, permissions=WORKSPACE_USER_PERMISSION_GUEST
    )
    for table in tables:
        TableGrant.objects.create(
            workspace_user=workspace_user, table=table, level=TableAccessLevel.VIEWER
        )
    return guest


@pytest.fixture
def two_databases(data_fixture):
    """Two databases with one table each and one guest granted each table."""

    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    first_database = data_fixture.create_database_application(workspace=workspace)
    second_database = data_fixture.create_database_application(workspace=workspace)
    first_table = data_fixture.create_database_table(database=first_database)
    second_table = data_fixture.create_database_table(database=second_database)
    return {
        "workspace": workspace,
        "first_database": first_database,
        "second_database": second_database,
        "first_guest": make_guest(data_fixture, workspace, first_table),
        "second_guest": make_guest(data_fixture, workspace, second_table),
    }


def database_checks(guest, *databases):
    return [
        PermissionCheck(guest, operation, database)
        for database in databases
        for operation in (
            ReadApplicationOperationType.type,
            ListTablesDatabaseTableOperationType.type,
        )
    ]


def decision(result):
    if result is True:
        return True
    assert isinstance(result, UserInvalidWorkspacePermissionsError)
    return False


def table_grants_manager():
    return permission_manager_type_registry.get("table_grants")


# -- database-scoped checks -------------------------------------------------


@pytest.mark.django_db
def test_a_guest_batch_answers_like_the_checks_one_by_one(two_databases):
    workspace = two_databases["workspace"]
    first, second = two_databases["first_database"], two_databases["second_database"]
    checks = database_checks(two_databases["first_guest"], first, second)
    checks += database_checks(two_databases["second_guest"], first, second)

    one_by_one = {}
    for check in checks:
        with local_cache.context():
            result = table_grants_manager().check_multiple_permissions(
                [check], workspace=workspace
            )
        one_by_one[check] = decision(result[check])

    with local_cache.context():
        batch = table_grants_manager().check_multiple_permissions(
            checks, workspace=workspace
        )

    assert {check: decision(result) for check, result in batch.items()} == one_by_one
    # Each guest reaches only the database holding their table, and two guests
    # in one batch do not share each other's answer.
    assert list(one_by_one.values()) == [
        True,
        True,
        False,
        False,
        False,
        False,
        True,
        True,
    ]


@pytest.mark.django_db
def test_a_guest_batch_costs_the_same_queries_as_a_single_check(two_databases):
    workspace = two_databases["workspace"]
    checks = database_checks(
        two_databases["first_guest"],
        two_databases["first_database"],
        two_databases["second_database"],
    )
    assert len(checks) == 4

    with local_cache.context(), CaptureQueriesContext(connection) as single:
        table_grants_manager().check_multiple_permissions(
            checks[:1], workspace=workspace
        )
    with local_cache.context(), CaptureQueriesContext(connection) as batch:
        table_grants_manager().check_multiple_permissions(checks, workspace=workspace)

    assert len(batch.captured_queries) == len(single.captured_queries)


# -- the hidden-field hook --------------------------------------------------


@pytest.mark.django_db
def test_the_hook_reuses_a_members_role_cached_by_a_check(
    data_fixture, django_assert_num_queries
):
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    table = data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=workspace)
    )
    member = data_fixture.create_user()
    data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )
    table = Table.objects.select_related("database").get(id=table.id)

    with local_cache.context():
        CoreHandler().check_permissions(
            member, ListFieldsOperationType.type, workspace=workspace, context=table
        )
        with django_assert_num_queries(0):
            assert hidden_field_ids_for_guest(member, table) == set()


@pytest.fixture
def guest_with_links(data_fixture):
    """A granted table whose fields read into a granted and an ungranted table.

    The expected hidden set is the link to the ungranted table and the lookup
    through it; the link to the granted table, the lookup through that one and
    a formula over the table's own field all stay visible.
    """

    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    granted = data_fixture.create_database_table(database=database)
    also_granted = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=granted, name="Name", primary=True)
    also_granted_name = data_fixture.create_text_field(
        table=also_granted, name="Name", primary=True
    )
    data_fixture.create_text_field(table=secret, name="Name", primary=True)
    salary = data_fixture.create_text_field(table=secret, name="Salary")

    handler = FieldHandler()
    secret_link = handler.create_field(
        admin, granted, "link_row", name="Secret link", link_row_table=secret
    )
    granted_link = handler.create_field(
        admin, granted, "link_row", name="Granted link", link_row_table=also_granted
    )
    secret_lookup = handler.create_field(
        admin,
        granted,
        "lookup",
        name="Salary lookup",
        through_field_id=secret_link.id,
        target_field_id=salary.id,
    )
    handler.create_field(
        admin,
        granted,
        "lookup",
        name="Granted lookup",
        through_field_id=granted_link.id,
        target_field_id=also_granted_name.id,
    )
    handler.create_field(
        admin, granted, "formula", name="Own formula", formula="field('Name')"
    )

    guest = make_guest(data_fixture, workspace, granted, also_granted)
    return {
        "workspace": workspace,
        "guest": guest,
        "table": Table.objects.select_related("database").get(id=granted.id),
        "hidden": {secret_link.id, secret_lookup.id},
    }


@pytest.mark.django_db
def test_the_hook_hides_what_reads_outside_the_grant(guest_with_links):
    with local_cache.context():
        hidden = hidden_field_ids_for_guest(
            guest_with_links["guest"], guest_with_links["table"]
        )

    assert hidden == guest_with_links["hidden"]


@pytest.mark.django_db
def test_the_hook_after_a_check_hides_the_same_fields_from_the_cache(
    guest_with_links, django_assert_num_queries
):
    guest, table = guest_with_links["guest"], guest_with_links["table"]

    with local_cache.context():
        CoreHandler().check_permissions(
            guest,
            ListFieldsOperationType.type,
            workspace=guest_with_links["workspace"],
            context=table,
        )
        # Role and grants come from the check's cache; only the table's link
        # fields and its dependency graph are read.
        with django_assert_num_queries(2):
            hidden = hidden_field_ids_for_guest(guest, table)

    assert hidden == guest_with_links["hidden"]


# -- the admin API ----------------------------------------------------------

INVITATION_BASE_URL = "http://localhost:3000/workspace-invitation"


def access_url(workspace):
    return reverse("api:arabase:table_access", kwargs={"workspace_id": workspace.id})


def guest_url(workspace, workspace_user):
    return reverse(
        "api:arabase:table_access_guest",
        kwargs={"workspace_id": workspace.id, "workspace_user_id": workspace_user.id},
    )


def table_entry(table, level):
    return {
        "table_id": table.id,
        "name": table.name,
        "database_id": table.database_id,
        "level": level,
    }


def rendered(payload):
    """The exact bytes the API's JSON renderer produces for `payload`."""

    return JSONRenderer().render(payload)


def invite(api_client, admin_api, email, entries):
    return api_client.post(
        access_url(admin_api["workspace"]),
        {"email": email, "tables": entries, "base_url": INVITATION_BASE_URL},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_api['token']}",
    )


def viewer_entries(*tables):
    return [{"table_id": table.id, "level": "VIEWER"} for table in tables]


@pytest.fixture
def admin_api(data_fixture):
    """A workspace admin with a token and three tables over two databases."""

    admin, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=admin)
    first_database = data_fixture.create_database_application(workspace=workspace)
    second_database = data_fixture.create_database_application(workspace=workspace)
    return {
        "admin": admin,
        "token": token,
        "workspace": workspace,
        "tables": [
            data_fixture.create_database_table(database=first_database, name="العملاء"),
            data_fixture.create_database_table(database=first_database, name="Orders"),
            data_fixture.create_database_table(database=second_database, name="Stock"),
        ],
    }


@pytest.mark.django_db
def test_the_invite_answers_with_the_exact_invitation_json(api_client, admin_api):
    first, second, third = admin_api["tables"]

    response = invite(
        api_client,
        admin_api,
        "guest@example.com",
        [
            {"table_id": third.id, "level": "EDITOR"},
            {"table_id": first.id},
            {"table_id": second.id, "level": "EDITOR"},
        ],
    )

    assert response.status_code == HTTP_200_OK
    invitation = WorkspaceInvitation.objects.get(email="guest@example.com")
    assert response.content == rendered(
        {
            "id": invitation.id,
            "email": "guest@example.com",
            "created_on": invitation.created_on,
            "tables": [
                table_entry(third, "EDITOR"),
                table_entry(first, "VIEWER"),
                table_entry(second, "EDITOR"),
            ],
        }
    )


@pytest.mark.django_db
def test_inviting_the_same_address_again_answers_with_only_the_new_tables(
    api_client, admin_api
):
    first, second, third = admin_api["tables"]
    invite(api_client, admin_api, "guest@example.com", viewer_entries(first, second))

    response = invite(
        api_client,
        admin_api,
        "guest@example.com",
        [{"table_id": third.id, "level": "EDITOR"}],
    )

    assert response.status_code == HTTP_200_OK
    invitation = WorkspaceInvitation.objects.get(email="guest@example.com")
    assert response.content == rendered(
        {
            "id": invitation.id,
            "email": "guest@example.com",
            "created_on": invitation.created_on,
            "tables": [table_entry(third, "EDITOR")],
        }
    )


@pytest.mark.django_db
def test_the_invite_costs_the_same_queries_for_one_and_three_tables(
    api_client, admin_api
):
    tables = admin_api["tables"]
    # Warm the per-process caches so that neither measured request pays for them.
    invite(api_client, admin_api, "warm-up@example.com", viewer_entries(tables[0]))

    with CaptureQueriesContext(connection) as one_table:
        response = invite(
            api_client, admin_api, "one@example.com", viewer_entries(tables[0])
        )
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["tables"]) == 1

    with CaptureQueriesContext(connection) as three_tables:
        response = invite(
            api_client, admin_api, "three@example.com", viewer_entries(*tables)
        )
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["tables"]) == 3

    assert len(three_tables.captured_queries) == len(one_table.captured_queries)


@pytest.mark.django_db
def test_the_listing_answers_with_the_exact_guests_and_invitations_json(
    api_client, data_fixture, admin_api
):
    first, second, third = admin_api["tables"]
    workspace = admin_api["workspace"]
    guest = data_fixture.create_user(first_name="ضيف")
    membership = data_fixture.create_user_workspace(
        workspace=workspace, user=guest, permissions=WORKSPACE_USER_PERMISSION_GUEST
    )
    TableGrant.objects.create(
        workspace_user=membership, table=third, level=TableAccessLevel.EDITOR
    )
    TableGrant.objects.create(
        workspace_user=membership, table=first, level=TableAccessLevel.VIEWER
    )
    parked = make_guest(data_fixture, workspace)
    parked_membership = WorkspaceUser.objects.get(workspace=workspace, user=parked)
    # A normal member and a normal invitation are not table guests.
    data_fixture.create_user_workspace(
        workspace=workspace, user=data_fixture.create_user(), permissions="MEMBER"
    )
    CoreHandler().create_workspace_invitation(
        user=admin_api["admin"],
        workspace=workspace,
        email="member@example.com",
        permissions="MEMBER",
        base_url=INVITATION_BASE_URL,
    )
    invitation = TableAccessHandler().invite_guest(
        user=admin_api["admin"],
        workspace=workspace,
        email="invited@example.com",
        tables=[
            {"table_id": second.id, "level": TableAccessLevel.EDITOR},
            {"table_id": first.id, "level": TableAccessLevel.VIEWER},
        ],
        base_url=INVITATION_BASE_URL,
    )
    invitation = WorkspaceInvitation.objects.get(id=invitation.id)

    response = api_client.get(
        access_url(workspace), HTTP_AUTHORIZATION=f"JWT {admin_api['token']}"
    )

    assert response.status_code == HTTP_200_OK
    assert response.content == rendered(
        {
            "guests": [
                {
                    "workspace_user_id": membership.id,
                    "user_id": guest.id,
                    "email": guest.email,
                    "name": "ضيف",
                    "tables": [
                        table_entry(third, "EDITOR"),
                        table_entry(first, "VIEWER"),
                    ],
                },
                {
                    "workspace_user_id": parked_membership.id,
                    "user_id": parked.id,
                    "email": parked.email,
                    "name": parked.first_name,
                    "tables": [],
                },
            ],
            "invitations": [
                {
                    "id": invitation.id,
                    "email": "invited@example.com",
                    "created_on": invitation.created_on,
                    "tables": [
                        table_entry(second, "EDITOR"),
                        table_entry(first, "VIEWER"),
                    ],
                }
            ],
        }
    )


@pytest.mark.django_db
def test_replacing_the_tables_answers_with_the_exact_guest_json(
    api_client, data_fixture, admin_api
):
    first, second, third = admin_api["tables"]
    workspace = admin_api["workspace"]
    guest = make_guest(data_fixture, workspace, first)
    membership = WorkspaceUser.objects.get(workspace=workspace, user=guest)

    response = api_client.patch(
        guest_url(workspace, membership),
        {
            "tables": [
                {"table_id": third.id, "level": "EDITOR"},
                {"table_id": second.id},
            ]
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_api['token']}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.content == rendered(
        {
            "workspace_user_id": membership.id,
            "user_id": guest.id,
            "email": guest.email,
            "name": guest.first_name,
            "tables": [table_entry(third, "EDITOR"), table_entry(second, "VIEWER")],
        }
    )
