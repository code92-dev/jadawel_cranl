import json
from copy import deepcopy
from typing import Any, Never

from arabase.mcp.protection.models import (
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.policy_state import (
    MCPProtectedFieldBinding,
    MCPProtectionPolicyState,
    _safe_field_type_name,
)
from arabase.mcp.protection.vault import (
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    get_mask_token_vault,
)
from jadawel.contrib.database.fields.dependencies.models import FieldDependency
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.table.models import Table
from jadawel.core.mcp.errors import MCPErrorCode, SafeMCPToolError
from jadawel.core.mcp.models import MCPEndpoint

MAX_ROWS_PER_CALL = 200
MAX_ISSUED_OR_REDEEMED_PER_CALL = 1000
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def table_has_protected_output(
    table_id: int, protected_fields, workspace_id: int
) -> bool:
    """Return whether direct or transitive protected data can leave this table."""

    direct_fields = tuple(
        field for field in protected_fields if field.table_id == table_id
    )
    return bool(
        _protected_output_fields(
            table_id, direct_fields, protected_fields, workspace_id
        )
    )


def mask_direct_row_output(
    endpoint: MCPEndpoint,
    args: Any,
    result: Any,
    policy: MCPProtectionPolicyState,
) -> Any:
    """Replace direct protected cells with fresh same-cell mask tokens."""

    table_id = args.table_id
    direct_fields = tuple(
        field for field in policy.protected_fields if field.table_id == table_id
    )
    table = Table.objects.get(id=table_id, database__workspace_id=endpoint.workspace_id)
    fields = _protected_output_fields(
        table_id, direct_fields, policy.protected_fields, endpoint.workspace_id
    )
    if not fields:
        return result

    output = deepcopy(result)
    rows = output["results"] if isinstance(output, dict) else output
    if not isinstance(rows, list):
        _raise_protection_unavailable()
    if len(rows) > MAX_ROWS_PER_CALL:
        _raise_protection_unavailable()

    model = table.get_model()
    row_ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != len(rows) or any(row_id is None for row_id in row_ids):
        _raise_protection_unavailable()
    observed_rows = model.objects.in_bulk(row_ids)
    if len(observed_rows) != len(row_ids):
        _raise_protection_unavailable()
    non_empty_values = 0
    for row in rows:
        for field in fields:
            if field.field_name not in row:
                _raise_protection_unavailable()
            if not _is_empty_value(row[field.field_name]):
                non_empty_values += 1
    if non_empty_values > MAX_ISSUED_OR_REDEEMED_PER_CALL:
        _raise_protection_unavailable()

    vault = None
    issued_digests: list[str] = []
    try:
        vault = get_mask_token_vault()
        issue_requests = []
        issue_targets = []
        with vault.issuance_lease(endpoint.id):
            for row in rows:
                observed_row = observed_rows[row["id"]]
                observed_state = observed_row.updated_on.isoformat()
                for field in fields:
                    if field.field_name not in row:
                        _raise_protection_unavailable()
                    value = row[field.field_name]
                    if _is_empty_value(value):
                        continue
                    issue_requests.append(
                        (
                            MaskTokenBinding(
                                endpoint_id=endpoint.id,
                                workspace_id=endpoint.workspace_id,
                                table_id=table_id,
                                row_id=row["id"],
                                field_id=field.field_id,
                                policy_revision=policy.revision,
                                access_generation=policy.access_generation,
                                operation_class=field.operation_class,
                                observed_row_state=observed_state,
                                field_type=field.field_type,
                            ),
                            value,
                        )
                    )
                    issue_targets.append((row, field.field_name))
            issued_tokens = vault.issue_many(issue_requests)
            for (row, field_name), issued in zip(
                issue_targets, issued_tokens, strict=True
            ):
                issued_digests.append(issued.digest)
                row[field_name] = issued.envelope
                if len(issued_digests) > MAX_ISSUED_OR_REDEEMED_PER_CALL:
                    _raise_protection_unavailable()
        _assert_policy_unchanged(endpoint, policy)
        if (
            len(
                json.dumps(
                    output,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode()
            )
            > MAX_RESPONSE_BYTES
        ):
            _raise_protection_unavailable()
    except (MaskTokenVaultUnavailable, SafeMCPToolError):
        if vault is not None:
            vault.delete(issued_digests)
        _raise_protection_unavailable()
    return output


def _protected_output_fields(
    table_id: int, direct_fields, protected_fields, workspace_id: int
):
    """Include derived fields whose dependency graph contains a protected leaf."""
    all_fields = list(
        Field.objects.filter(
            table__database__workspace_id=workspace_id, trashed=False
        ).prefetch_related("field_dependencies")
    )
    protected_ids = {field.field_id for field in protected_fields}
    broken_dependant_ids = set(
        FieldDependency.objects.filter(
            dependant__table__database__workspace_id=workspace_id,
            dependency__isnull=True,
        ).values_list("dependant_id", flat=True)
    )
    direct_by_id = {field.field_id: field for field in direct_fields}
    dependencies = {
        field.id: {dependency.id for dependency in field.field_dependencies.all()}
        for field in all_fields
    }
    known_field_ids = set(dependencies)
    derived_ids = set()
    changed = True
    while changed:
        changed = False
        for field_id, field_dependencies in dependencies.items():
            if field_id in protected_ids or field_id in derived_ids:
                continue
            if field_dependencies & (protected_ids | derived_ids):
                derived_ids.add(field_id)
                changed = True

    # A cycle makes the dependency provenance unprovable.  Restrict the check
    # to the protected lineage so an unrelated broken formula elsewhere in the
    # workspace does not take every protected table offline.
    affected_ids = protected_ids | derived_ids
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(field_id: int) -> None:
        if field_id in visiting:
            _raise_protection_unavailable()
        if field_id in visited:
            return
        visiting.add(field_id)
        for dependency_id in dependencies.get(field_id, ()):
            if dependency_id in affected_ids:
                visit(dependency_id)
            elif dependency_id not in known_field_ids:
                # A dependency that disappeared from the active field graph
                # cannot be proven public or protected.
                _raise_protection_unavailable()
        visiting.remove(field_id)
        visited.add(field_id)

    for field_id in affected_ids:
        visit(field_id)
    # A broken reference is only relevant when it belongs to a protected leaf
    # or to a derived field whose value is transitively protected.  An unrelated
    # broken formula elsewhere in the workspace must not make every protected
    # table unreadable; the affected field itself remains fail-closed.
    if broken_dependant_ids & (protected_ids | derived_ids):
        _raise_protection_unavailable()
    output_fields = list(direct_fields)
    for field in all_fields:
        # A dependency may live in another table (for example through a link
        # field), but only fields materialized in this row payload can be
        # masked here.  Carrying a cross-table dependant into the output list
        # would make an otherwise valid response fail because its key is not
        # present in the target table's serialized row.
        if field.table_id == table_id and field.id in derived_ids:
            output_fields.append(
                MCPProtectedFieldBinding(
                    field_id=field.id,
                    table_id=field.table_id,
                    field_name=field.name,
                    field_type=_safe_field_type_name(field),
                )
            )
    return tuple(
        _OutputField(
            binding=field,
            operation_class="preserve_cell"
            if field.field_id in direct_by_id
            else "display_only",
        )
        for field in output_fields
    )


class _OutputField:
    __slots__ = ("binding", "operation_class")

    def __init__(self, *, binding, operation_class: str):
        self.binding = binding
        self.operation_class = operation_class

    @property
    def field_id(self):
        return self.binding.field_id

    @property
    def field_name(self):
        return self.binding.field_name

    @property
    def field_type(self):
        return self.binding.field_type


def _assert_policy_unchanged(
    endpoint: MCPEndpoint, snapshot: MCPProtectionPolicyState
) -> None:
    try:
        current = MCPProtectionPolicy.objects.get(
            id=snapshot.policy_id,
            endpoint=endpoint,
            revision=snapshot.revision,
            access_generation=snapshot.access_generation,
            lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
            safe_reason_code=MCPProtectionSafeReason.NONE,
        )
    except MCPProtectionPolicy.DoesNotExist:
        _raise_protection_unavailable()
    current_field_ids = set(
        current.protected_fields.filter(
            state=MCPProtectedFieldState.ACTIVE
        ).values_list("field_id", flat=True)
    )
    if current_field_ids != {field.field_id for field in snapshot.protected_fields}:
        _raise_protection_unavailable()


def _is_empty_value(value: Any) -> bool:
    return (
        value is None
        or value == ""
        or (isinstance(value, (list, dict, tuple)) and len(value) == 0)
    )


def _raise_protection_unavailable() -> Never:
    raise SafeMCPToolError(MCPErrorCode.PROTECTION_UNAVAILABLE, retryable=False)
