"""Characterization of the policy snapshot loader used by every MCP call.

The snapshot must keep the relation's ``field_id`` ordering across tables, keep
the resolved field type names, include trashed rows in the join (so a trashed
table fails closed instead of disappearing) and stay a fixed number of queries.
"""

import pytest

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.policy_state import (
    MCPProtectedFieldBinding,
    get_mcp_protection_policy_state,
)
from jadawel.contrib.database.table.models import Table
from jadawel.core.mcp.errors import MCPErrorCode, SafeMCPToolError


def _two_table_policy(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    first_table = data_fixture.create_database_table(database=database)
    second_table = data_fixture.create_database_table(database=database)
    first_text = data_fixture.create_text_field(name="Secret", table=first_table)
    second_number = data_fixture.create_number_field(name="Salary", table=second_table)
    first_number = data_fixture.create_number_field(name="Score", table=first_table)
    policy = endpoint.arabase_protection_policy
    # Insert out of field-id order: the snapshot must still follow field_id.
    for field in (first_number, second_number, first_text):
        MCPProtectedField.objects.create(policy=policy, field=field)
    return endpoint, first_table, (first_text, second_number, first_number)


@pytest.mark.django_db
def test_snapshot_bindings_follow_field_id_order_across_tables(data_fixture):
    endpoint, _, fields = _two_table_policy(data_fixture)

    state = get_mcp_protection_policy_state(endpoint)

    assert state.has_protected_fields is True
    assert state.protected_fields == tuple(
        MCPProtectedFieldBinding(
            field_id=field.id,
            table_id=field.table_id,
            field_name=field.name,
            field_type=field_type,
        )
        for field, field_type in sorted(
            zip(fields, ("text", "number", "number"), strict=True),
            key=lambda item: item[0].id,
        )
    )
    assert [binding.field_type for binding in state.protected_fields] == [
        "text",
        "number",
        "number",
    ]


@pytest.mark.django_db
def test_snapshot_uses_a_fixed_number_of_queries(
    data_fixture, django_assert_num_queries
):
    endpoint, _, _ = _two_table_policy(data_fixture)
    # Warm the content-type cache the field adapters resolve through.
    get_mcp_protection_policy_state(endpoint)

    # The nested prefetch ("protected_fields__field__table__database") took 5
    # queries: the policy, then one per prefetched level.  Loading the
    # relations with a single select_related join takes 2.
    with django_assert_num_queries(2):
        state = get_mcp_protection_policy_state(endpoint)

    assert len(state.protected_fields) == 3


@pytest.mark.django_db
def test_snapshot_fails_closed_for_a_trashed_table(data_fixture):
    endpoint, first_table, _ = _two_table_policy(data_fixture)
    # Update directly so no lifecycle receiver runs: the loader itself must see
    # the trashed row rather than silently dropping the relation.
    Table.objects_and_trash.filter(id=first_table.id).update(trashed=True)

    with pytest.raises(SafeMCPToolError) as exc_info:
        get_mcp_protection_policy_state(endpoint)

    assert exc_info.value.code is MCPErrorCode.PROTECTION_UNAVAILABLE
    assert exc_info.value.retryable is False


@pytest.mark.django_db
def test_snapshot_fails_closed_for_a_suspended_relation(data_fixture):
    endpoint, _, fields = _two_table_policy(data_fixture)
    MCPProtectedField.objects.filter(field=fields[1]).update(
        state=MCPProtectedFieldState.SUSPENDED,
        safe_reason_code=MCPProtectionSafeReason.FIELD_TYPE_CONVERSION_UNSUPPORTED,
    )

    with pytest.raises(SafeMCPToolError) as exc_info:
        get_mcp_protection_policy_state(endpoint)

    assert exc_info.value.code is MCPErrorCode.PROTECTION_UNAVAILABLE
    assert exc_info.value.retryable is False
