"""Table-scoped guest access (docs/TABLE_LEVEL_ACCESS_PLAN.md).

Jadawel's OSS roles are workspace-wide: being a member means seeing every
database and every table in the workspace. This manager adds a fourth role,
``GUEST``, whose visible surface is exactly the tables listed in
``arabase.table_access.models.TableGrant``.

Two properties make it safe to add a role this way:

* **It only speaks for guests.** For any other role the manager returns ``{}``
  and every decision falls through to core untouched, exactly like
  ``arabase.permissions.viewer_role``.
* **For a guest it answers every check.** The manager is an allowlist, not a
  deny-list: an operation it does not recognise is denied. A deny-list would
  silently permit every operation added upstream later, which is the wrong
  default for a role whose whole purpose is to *not* see things.

The manager is inserted before core's ``basic`` in
``settings.PERMISSION_MANAGERS`` from ``ArabaseConfig.ready()``, so a guest's
denial is the first definitive answer and no core file is edited.
"""

from typing import Any, Dict, Iterable, List, Optional, Set

from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST
from arabase.table_access.models import TableAccessLevel, TableGrant
from jadawel.core.cache import local_cache
from jadawel.core.exceptions import UserInvalidWorkspacePermissionsError
from jadawel.core.models import WorkspaceUser
from jadawel.core.registries import PermissionManagerType, object_scope_type_registry
from jadawel.core.subjects import UserSubjectType

# Operations whose context is the workspace or a database rather than a table.
# A guest needs these few to boot the app shell and render the sidebar; the
# database-scoped ones are additionally gated on the database holding at least
# one granted table (see `_check`).
WORKSPACE_LEVEL_ALLOWED: Set[str] = {
    "workspace.read",
    "workspace.list_applications",
    "application.read",
    "database.list_tables",
}

# Read-only access to a granted table.
VIEWER_ALLOWED: Set[str] = {
    "database.table.read",
    "database.table.list_rows",
    "database.table.list_row_names",
    "database.table.list_fields",
    "database.table.field.read",
    # The per-table websocket page, so a guest's grid updates live like
    # everyone else's. Subscribing to it is permission checked, which is what
    # keeps realtime inside the grant.
    "database.table.listen_to_all",
    "database.table.list_views",
    "database.table.read_view_order",
    "database.table.read_row",
    "database.table.read_adjacent_row",
    "database.table.view.read",
    "database.table.view.list_rows",
    "database.table.view.read_row",
    "database.table.view.read_adjacent_row",
    "database.table.view.list_fields",
    "database.table.view.read_field_options",
    "database.table.view.read_default_values",
    "database.table.view.list_filter",
    "database.table.view.filter.read",
    "database.table.view.list_sort",
    "database.table.view.sort.read",
    "database.table.view.list_group_bys",
    "database.table.view.group_by.read",
    "database.table.view.list_aggregations",
    "database.table.view.read_aggregation",
}

# Row data on top of everything a viewer may do. Schema — fields, views, the
# table itself — stays out of both levels.
EDITOR_ALLOWED: Set[str] = VIEWER_ALLOWED | {
    "database.table.create_row",
    "database.table.update_row",
    "database.table.delete_row",
    "database.table.move_row",
    "database.table.read_row_history",
    "database.table.view.create_row",
    "database.table.view.update_row",
    "database.table.view.delete_row",
}

ALLOWED_BY_LEVEL: Dict[str, Set[str]] = {
    TableAccessLevel.VIEWER: VIEWER_ALLOWED,
    TableAccessLevel.EDITOR: EDITOR_ALLOWED,
}


# -- request-scoped lookups ----------------------------------------------------
#
# Shared by the manager below and by the hidden-field hook
# (`arabase.table_access.hidden_fields`), which runs for every field listing and
# row payload right after the permission check that filled these caches.


def workspace_roles(
    workspace_id: int, user_ids: Iterable[int], include_trash: bool = False
) -> Dict[int, Any]:
    """Map of user id -> workspace role, covering at least `user_ids`.

    Request-scoped, because the manager sits in front of every check and every
    listing: without the cache a single request pays one query per call site,
    which showed up as a doubled query count in core's workspace search budget.
    `None` is cached too — it is the answer for a user who is not in the
    workspace at all, and it must not be re-queried either.
    """

    cached = local_cache.get(f"arabase_table_access_roles_{workspace_id}", dict)

    missing = [user_id for user_id in user_ids if user_id not in cached]
    if missing:
        manager = (
            WorkspaceUser.objects_and_trash if include_trash else WorkspaceUser.objects
        )
        found = dict(
            manager.filter(workspace_id=workspace_id, user_id__in=missing).values_list(
                "user_id", "permissions"
            )
        )
        for user_id in missing:
            cached[user_id] = found.get(user_id)

    return cached


def table_grants_for(
    workspace_id: int, user_ids: Iterable[int], include_trash: bool = False
) -> Dict[int, Dict[int, str]]:
    """Map of user id -> {table id: level} for the given guests.

    Cached per request for the same reason as `workspace_roles`, and only ever
    reached for a user already known to be a guest.
    """

    cached = local_cache.get(f"arabase_table_access_grants_{workspace_id}", dict)

    missing = [user_id for user_id in user_ids if user_id not in cached]
    if missing:
        manager = (
            WorkspaceUser.objects_and_trash if include_trash else WorkspaceUser.objects
        )
        workspace_user_ids = dict(
            manager.filter(workspace_id=workspace_id, user_id__in=missing).values_list(
                "id", "user_id"
            )
        )
        for user_id in missing:
            cached[user_id] = {}
        rows = TableGrant.objects.filter(
            workspace_user_id__in=workspace_user_ids.keys()
        ).values_list("workspace_user_id", "table_id", "level")
        for workspace_user_id, table_id, level in rows:
            cached[workspace_user_ids[workspace_user_id]][table_id] = level

    return {user_id: cached[user_id] for user_id in user_ids}


class TableGrantPermissionManagerType(PermissionManagerType):
    """Narrows a GUEST member's workspace down to the tables they were granted."""

    type = "table_grants"
    supported_actor_types = [UserSubjectType.type]

    # -- lookups ---------------------------------------------------------

    def _roles(self, workspace, actors, include_trash=False) -> Dict[int, Any]:
        """Map of user id -> workspace role; see `workspace_roles`."""

        return workspace_roles(
            workspace.id, [actor.id for actor in actors], include_trash
        )

    def _guest_user_ids(self, workspace, actors, include_trash=False) -> Set[int]:
        """The subset of `actors` that hold the GUEST role in this workspace."""

        roles = self._roles(workspace, actors, include_trash)
        return {
            actor.id
            for actor in actors
            if roles.get(actor.id) == WORKSPACE_USER_PERMISSION_GUEST
        }

    def _grants(self, workspace, user_ids, include_trash=False):
        """Map of user id -> {table id: level}; see `table_grants_for`."""

        return table_grants_for(workspace.id, user_ids, include_trash)

    def _scope_of(self, context: Any, cache: Dict[Any, Any]):
        """Resolve a check context to ``(table_id, database_id)``.

        Either may be ``None``: a workspace-scoped context has neither, a
        database-scoped context has only the database. Walking the scope
        hierarchy means this works for any context — a view, a field, a filter,
        a row — without this module knowing those models.
        """

        if context is None:
            return None, None

        key = (type(context), getattr(context, "id", None))
        if key in cache:
            return cache[key]

        try:
            scope_type = object_scope_type_registry.get_by_model(context)
        except Exception:  # noqa: BLE001 - unregistered scope: treat as unknown
            cache[key] = (None, None)
            return cache[key]

        from jadawel.contrib.database.models import Table
        from jadawel.core.models import Application

        candidates = [context] + list(scope_type.get_parents(context))

        table_id = None
        database_id = None
        for candidate in candidates:
            if isinstance(candidate, Table):
                table_id = candidate.id
                database_id = candidate.database_id
            elif isinstance(candidate, Application) and database_id is None:
                # `Database` inherits from `Application` and shares its primary
                # key, so a base `Application` context resolves to the same id
                # a `Database` one would.
                database_id = candidate.id

        cache[key] = (table_id, database_id)
        return cache[key]

    # -- decisions -------------------------------------------------------

    def _check(self, check, grants: Dict[int, str], cache) -> Optional[bool]:
        table_id, database_id = self._scope_of(check.context, cache)

        if table_id is not None:
            level = grants.get(table_id)
            if level is None:
                return False
            return check.operation_name in ALLOWED_BY_LEVEL.get(level, set())

        if check.operation_name not in WORKSPACE_LEVEL_ALLOWED:
            return False

        if database_id is not None:
            # A database-scoped operation is only allowed for a database that
            # actually holds one of the guest's tables, otherwise `application
            # .read` would expose every database in the workspace.
            return database_id in self._granted_database_ids(grants, cache)

        return True

    def _granted_database_ids(
        self, grants: Dict[int, str], cache: Optional[Dict[Any, Any]] = None
    ) -> Set[int]:
        """The databases holding at least one of the granted tables.

        With `cache` — the per-call dict of `check_multiple_permissions` — the
        answer is memoised per set of granted tables, so a batch of
        database-scoped checks pays one query instead of one per check.
        """

        from jadawel.contrib.database.models import Table

        if not grants:
            return set()

        key = ("granted_database_ids", frozenset(grants))
        if cache is not None and key in cache:
            return cache[key]

        database_ids = set(
            Table.objects.filter(id__in=grants.keys()).values_list(
                "database_id", flat=True
            )
        )
        if cache is not None:
            cache[key] = database_ids
        return database_ids

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        if workspace is None or not checks:
            return {}

        guest_ids = self._guest_user_ids(
            workspace, {check.actor for check in checks}, include_trash
        )
        if not guest_ids:
            return {}

        grants_by_user = self._grants(workspace, guest_ids, include_trash)
        cache: Dict[Any, Any] = {}

        result = {}
        for check in checks:
            if check.actor.id not in guest_ids:
                continue
            allowed = self._check(check, grants_by_user[check.actor.id], cache)
            result[check] = (
                True
                if allowed
                else UserInvalidWorkspacePermissionsError(
                    check.actor, workspace, check.operation_name
                )
            )
        return result

    # -- listings --------------------------------------------------------

    def filter_queryset(self, actor, operation_name, queryset, workspace=None):
        if workspace is None:
            return None

        guest_ids = self._guest_user_ids(workspace, [actor])
        if not guest_ids:
            return None

        grants = self._grants(workspace, guest_ids)[actor.id]

        if operation_name in ("workspace.list_applications", "application.read"):
            return queryset.filter(id__in=self._granted_database_ids(grants))

        if operation_name == "database.list_tables":
            return queryset.filter(id__in=list(grants.keys()))

        # Any other listing is not part of a guest's surface. Returning an
        # empty queryset is the allowlist stance: a list we have not reviewed
        # must not leak rows from tables the guest was never granted.
        return queryset.none()

    # -- frontend --------------------------------------------------------

    def get_permissions_object(self, actor, workspace=None, include_trash=False):
        if workspace is None:
            return None

        guest_ids = self._guest_user_ids(workspace, [actor], include_trash)
        if not guest_ids:
            return None

        grants = self._grants(workspace, guest_ids, include_trash)[actor.id]
        return {
            "is_guest": True,
            "table_grants": {
                str(table_id): level for table_id, level in grants.items()
            },
        }

    def get_roles(self) -> List[str]:
        return [WORKSPACE_USER_PERMISSION_GUEST]
