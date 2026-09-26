"""Which fields of a granted table a guest must not see.

A table grant is only as tight as the fields inside it. A link row field
carries the primary-field values of rows in the table it points at; a lookup,
rollup, count or formula field can read values out of a table the guest was
never granted. Field listing and row serialization are all-or-nothing on the
table, so core calls this through the ``get_hidden_field_ids`` plugin hook (see
PATCHES.md) and excludes whatever it returns.

A field is hidden when it reads through to a table the guest does not hold,
which means granting the linked table too makes the field appear — the admin
decides how much of the graph a guest sees by choosing the tables.
"""

from typing import Any, Set

from arabase.permissions.table_grants import table_grants_for, workspace_roles
from arabase.table_access.constants import WORKSPACE_USER_PERMISSION_GUEST


def granted_table_ids(user: Any, workspace_id: int) -> Set[int]:
    """The tables `user` was granted, or none when they are not a guest.

    Reads the guest manager's request-scoped role and grant cache, which the
    permission check in front of every field listing and row payload has
    usually filled already.
    """

    role = workspace_roles(workspace_id, [user.id])[user.id]
    if role != WORKSPACE_USER_PERMISSION_GUEST:
        return set()
    return set(table_grants_for(workspace_id, [user.id])[user.id])


def hidden_field_ids_for_guest(user: Any, table: Any) -> Set[int]:
    """The fields of `table` that read outside the guest's granted tables."""

    if user is None or not getattr(user, "is_authenticated", False):
        return set()

    from jadawel.contrib.database.fields.dependencies.models import FieldDependency
    from jadawel.contrib.database.fields.models import LinkRowField

    granted = granted_table_ids(user, table.database.workspace_id)
    if not granted:
        # Not a guest at all, or a guest of no tables: core decides. Returning
        # an empty set here is what keeps this hook invisible to every normal
        # member.
        return set()

    hidden: Set[int] = set()

    for link_field in LinkRowField.objects.filter(table_id=table.id).only(
        "id", "link_row_table_id"
    ):
        if link_field.link_row_table_id not in granted:
            hidden.add(link_field.id)

    # Formulas, lookups, rollups and counts all land in the dependency graph,
    # so one query covers every type that can read across a table boundary --
    # including types added later.
    dependencies = FieldDependency.objects.filter(
        dependant__table_id=table.id
    ).select_related("dependency", "via")
    for dependency in dependencies:
        target = dependency.dependency
        if target is not None and target.table_id not in granted | {table.id}:
            hidden.add(dependency.dependant_id)
        via = dependency.via
        if via is not None and via.link_row_table_id not in granted:
            hidden.add(dependency.dependant_id)

    return hidden
