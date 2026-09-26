from contextlib import contextmanager

from django.db import connection
from django.test.utils import CaptureQueriesContext

import pytest

# Tables of the optional plugins under plugins/. When JADAWEL_PLUGIN_DIR loads
# them, their permission checks add queries to every request, so the protection
# query pins count only the queries of the application itself.
PLUGIN_TABLE_PREFIXES = ('"jadawel_organizations_', '"jadawel_billing_')


def _is_plugin_query(sql):
    return any(prefix in sql for prefix in PLUGIN_TABLE_PREFIXES)


@pytest.fixture
def django_assert_num_fork_queries():
    """Like ``django_assert_num_queries``, ignoring the optional plugins' queries."""

    @contextmanager
    def assert_num_queries(num):
        with CaptureQueriesContext(connection) as context:
            yield context
        queries = [
            query["sql"]
            for query in context.captured_queries
            if not _is_plugin_query(query["sql"])
        ]
        assert len(queries) == num, (
            f"Expected to perform {num} queries but {len(queries)} were done:\n\n"
            + "\n\n".join(queries)
        )

    return assert_num_queries
