"""Rows-added-per-day for the workspace home page's activity chart.

Companion to `database_stats`, and built the same way and for the same reason:
every Jadawel table is a real Postgres table, so the only honest source for "how
much did this workspace grow" is the rows themselves. `created_on` exists on
every user table, so a `GROUP BY` per table answers it exactly.

The alternatives were all worse:

* **`TableUsage`** carries a row count but no history, and is only written when
  the `track_workspace_usage` instance setting is on — off by default.
* **The audit log** would give a real event stream, but it is an enterprise
  feature and this fork must not read from `premium/` or `enterprise/`.
* **`RowHistory`** only records *changes* to existing rows, and is pruned on a
  retention schedule, so it under-counts creations and loses the older half of
  any window longer than the retention period.

Cost grows with the number of tables, exactly as it does for the counters, so the
fan-out is capped the same way and the response says plainly when it gave up
rather than returning a partial series that looks complete.
"""

from datetime import timedelta

from django.db import connection
from django.utils import timezone

from arabase.api.user_table_sql import union_all_per_table

# Matches `database_stats.MAX_TABLES_FOR_EXACT_COUNTS`. Kept as its own constant
# because the two queries are not the same cost — this one groups as well as
# counts — and tuning one should not silently retune the other.
MAX_TABLES_FOR_ACTIVITY = 200

DEFAULT_DAYS = 30
MAX_DAYS = 365


def _rows_created_per_day(table_ids, since):
    """`{date: count}` of non-trashed rows created on or after `since`.

    One round trip for every table, unioned by `union_all_per_table`, which
    explains why the table names are formatted rather than bound. `since` is the
    only user-influenced value, and it is passed as a real bound parameter, once
    per table.
    """

    if not table_ids:
        return {}

    per_table = union_all_per_table(
        table_ids,
        "SELECT created_on::date AS day, COUNT(*) AS c FROM {table} "
        "WHERE trashed = false AND created_on >= %s GROUP BY 1",
    )
    # noqa S608: `per_table` holds only int()-coerced table names; see above.
    sql = (
        "SELECT day, SUM(c) FROM ("  # noqa: S608
        + per_table
        + ") AS per_table GROUP BY day"
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, [since] * len(table_ids))
        return {row[0]: int(row[1]) for row in cursor.fetchall()}


def get_workspace_activity(tables, days=DEFAULT_DAYS):
    """Rows created per day over the last `days` days, oldest first.

    Returns a dense series — every day in the window is present, with `count: 0`
    for days nothing was added. A sparse series would make the chart draw a
    straight line across a quiet week, which reads as steady activity rather than
    none.

    `tables` must already be permission-filtered by the caller (see
    `database_stats.visible_tables`); this function does no access control of
    its own.
    """

    days = max(1, min(int(days), MAX_DAYS))

    # The window is whole days in the server's timezone, ending today. `days` of
    # history means today plus the previous `days - 1`.
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    table_ids = list(tables.filter(trashed=False).values_list("id", flat=True))
    complete = len(table_ids) <= MAX_TABLES_FOR_ACTIVITY

    counts = _rows_created_per_day(table_ids, start) if complete else {}

    series = [
        {
            "date": (start + timedelta(days=offset)).isoformat(),
            "count": counts.get(start + timedelta(days=offset), 0),
        }
        for offset in range(days)
    ]

    return {
        "days": days,
        "complete": complete,
        "total": sum(point["count"] for point in series),
        "series": series if complete else [],
    }
