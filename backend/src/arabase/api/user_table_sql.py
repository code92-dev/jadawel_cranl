"""Raw SQL across the per-table Postgres tables behind Jadawel's user tables.

The workspace home page counters (`database_stats`) and activity chart
(`activity`) each read every visible user table in one round trip, as one
`UNION ALL` of the same statement per table.
"""

from jadawel.contrib.database.table.constants import USER_TABLE_DATABASE_NAME_PREFIX


def union_all_per_table(table_ids, part):
    """`part` once per table id, joined with ` UNION ALL `.

    `part` is a `str.format` template: `{table}` is replaced by the table's
    Postgres name and `{table_id}` by its id.

    The statement is built by string formatting because the *table name* varies
    per part, and a table name cannot be a bound parameter in SQL. Table ids are
    forced through `int()` before they reach the string: they come from our own
    database, but they are the only interpolated values here and a stray
    non-integer would be an injection point. Anything else a caller needs in the
    statement must be passed to `cursor.execute` as a bound parameter.
    """

    return " UNION ALL ".join(
        part.format(
            table=f"{USER_TABLE_DATABASE_NAME_PREFIX}{int(table_id)}",
            table_id=int(table_id),
        )
        for table_id in table_ids
    )
