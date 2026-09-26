"""Per-database counters for the workspace home page.

The workspace page lists a workspace's databases and, in the Jadawel fork, shows
how much data each one holds. None of those numbers are available from the
existing application payload:

* **Tables** are serialized (`DatabaseSerializer.tables`), so the count is free
  client-side — it is included here anyway so one call answers the whole card.
* **Fields** are not serialized at all for the workspace listing.
* **Rows** have no cheap source. `TableUsage.row_count` exists but is written by
  the periodic `run_calculate_storage` task, which only runs when the instance
  setting `track_workspace_usage` is enabled — off by default, and it leaves the
  number up to 30 minutes stale even when on. A user who just imported rows would
  see a stale figure or none at all.

Every Jadawel table is a real Postgres table, so exact row counts mean one
`COUNT(*)` per table. Issued through the ORM that costs a dynamic model build per
table (~370ms for 14 tables, measured); issued as a single `UNION ALL` of plain
counts it is ~4ms for the same 14. This module does the latter.

The cost still grows linearly with the number of tables in the workspace, so the
fan-out is capped (`MAX_TABLES_FOR_EXACT_COUNTS`) and the response says plainly
whether the row numbers are exact, rather than silently returning a wrong total.
"""

from django.db import connection
from django.db.models import Count, Q, QuerySet

from arabase.api.user_table_sql import union_all_per_table
from jadawel.contrib.database.operations import ListTablesDatabaseTableOperationType
from jadawel.contrib.database.table.models import Table
from jadawel.core.handler import CoreHandler

# Above this many tables in a single workspace the UNION ALL stops being a cheap
# query. Callers get `rows_exact: false` and no row numbers rather than a slow
# page or a fabricated total.
MAX_TABLES_FOR_EXACT_COUNTS = 200


def visible_tables(user, workspace, databases) -> QuerySet:
    """The non-trashed tables in `databases` that `user` may list.

    Filtered through the same permission check as the sidebar's table list. A
    database being visible does not make every table in it visible: a GUEST
    member sees a database because it holds one granted table, and must not be
    handed counts for the tables beside it.
    """

    return CoreHandler().filter_queryset(
        user,
        ListTablesDatabaseTableOperationType.type,
        Table.objects.filter(database__in=databases, trashed=False),
        workspace=workspace,
    )


def _tables_by_database(database_ids, tables):
    """`{database_id: [table_id, ...]}` for `tables`, in one query."""

    tables_by_database = {database_id: [] for database_id in database_ids}
    rows = tables.filter(database_id__in=database_ids).values_list("id", "database_id")
    for table_id, database_id in rows:
        tables_by_database[database_id].append(table_id)
    return tables_by_database


def _field_counts(table_ids):
    """Non-trashed field count per table id, in one query."""

    if not table_ids:
        return {}

    rows = (
        Table.objects.filter(id__in=table_ids)
        .annotate(num_fields=Count("field", filter=Q(field__trashed=False)))
        .values_list("id", "num_fields")
    )
    return dict(rows)


def _row_counts(table_ids):
    """Exact non-trashed row count per table id, in one round trip.

    The statement comes from `union_all_per_table`, which explains why it is
    formatted rather than bound and why that is safe.
    """

    if not table_ids:
        return {}

    sql = union_all_per_table(
        table_ids,
        "SELECT {table_id} AS table_id, COUNT(*) AS row_count "
        "FROM {table} WHERE trashed = false",
    )

    with connection.cursor() as cursor:
        cursor.execute(sql)
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_database_stats(databases, tables):
    """Build `{database_id: {...counters}}` for the given database applications.

    `databases` and `tables` must already be permission-filtered by the caller —
    this function does no access control of its own. Only `tables` are counted;
    see `visible_tables`.
    """

    database_ids = [database.id for database in databases]
    if not database_ids:
        return {}

    tables_by_database = _tables_by_database(database_ids, tables)
    all_table_ids = [tid for ids in tables_by_database.values() for tid in ids]

    field_counts = _field_counts(all_table_ids)

    rows_exact = len(all_table_ids) <= MAX_TABLES_FOR_EXACT_COUNTS
    row_counts = _row_counts(all_table_ids) if rows_exact else {}

    return {
        database_id: {
            "table_count": len(table_ids),
            "field_count": sum(field_counts.get(t, 0) for t in table_ids),
            "row_count": (
                sum(row_counts.get(t, 0) for t in table_ids) if rows_exact else None
            ),
            "rows_exact": rows_exact,
        }
        for database_id, table_ids in tables_by_database.items()
    }
