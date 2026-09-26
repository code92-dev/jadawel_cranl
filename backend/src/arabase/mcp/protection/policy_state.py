from dataclasses import dataclass

from django.db.models import Prefetch

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from jadawel.contrib.database.fields.dependencies.models import FieldDependency
from jadawel.contrib.database.fields.models import Field
from jadawel.core.mcp.errors import MCPErrorCode, SafeMCPToolError
from jadawel.core.mcp.models import MCPEndpoint


@dataclass(frozen=True, slots=True)
class MCPProtectedFieldBinding:
    field_id: int
    table_id: int
    field_name: str
    field_type: str


@dataclass(frozen=True, slots=True)
class MCPProtectionPolicyState:
    """The immutable policy snapshot used by one intercepted MCP call."""

    policy_id: int = 0
    revision: int = 0
    access_generation: int = 0
    protected_fields: tuple[MCPProtectedFieldBinding, ...] = ()

    @property
    def has_protected_fields(self) -> bool:
        # The loader raises for every relation that is not ACTIVE, so a loaded
        # snapshot has protected fields exactly when it carries bindings.
        return bool(self.protected_fields)


def protection_unavailable() -> SafeMCPToolError:
    """Return the fixed fail-closed protection error for the caller to raise."""

    return SafeMCPToolError(MCPErrorCode.PROTECTION_UNAVAILABLE, retryable=False)


def get_mcp_protection_policy_state(
    endpoint: MCPEndpoint,
) -> MCPProtectionPolicyState:
    """Load and validate the endpoint's explicit policy for one MCP call."""

    try:
        # One join loads every relation with its field, table and database.
        # Joins never apply the trash-filtering default managers, so a trashed
        # field, table or database stays visible and fails closed below.
        policy = MCPProtectionPolicy.objects.prefetch_related(
            Prefetch(
                "protected_fields",
                queryset=MCPProtectedField.objects.select_related(
                    "field__table__database"
                ),
            )
        ).get(endpoint=endpoint)
    except MCPProtectionPolicy.DoesNotExist:
        raise protection_unavailable()

    if (
        policy.revision < 1
        or policy.access_generation < 1
        or policy.lifecycle_status != MCPProtectionLifecycleStatus.ACTIVE
        or policy.safe_reason_code != MCPProtectionSafeReason.NONE
    ):
        raise protection_unavailable()

    protected_fields = list(policy.protected_fields.all())
    for relation in protected_fields:
        if (
            relation.state
            not in (MCPProtectedFieldState.ACTIVE, MCPProtectedFieldState.SUSPENDED)
            or (
                relation.state == MCPProtectedFieldState.ACTIVE
                and relation.safe_reason_code != MCPProtectionSafeReason.NONE
            )
            or (
                relation.state == MCPProtectedFieldState.SUSPENDED
                and relation.safe_reason_code == MCPProtectionSafeReason.NONE
            )
            or relation.field.table.database.workspace_id != endpoint.workspace_id
            or relation.field.trashed
            or relation.field.table.trashed
            or relation.field.table.database.trashed
        ):
            raise protection_unavailable()

        if relation.state == MCPProtectedFieldState.SUSPENDED:
            raise protection_unavailable()

    bindings = tuple(
        MCPProtectedFieldBinding(
            field_id=relation.field_id,
            table_id=relation.field.table_id,
            field_name=relation.field.name,
            field_type=safe_field_type_name(relation.field),
        )
        for relation in protected_fields
        if relation.state == MCPProtectedFieldState.ACTIVE
    )
    return MCPProtectionPolicyState(
        policy_id=policy.id,
        revision=policy.revision,
        access_generation=policy.access_generation,
        protected_fields=bindings,
    )


def safe_field_type_name(field) -> str:
    """Resolve a protected field adapter without allowing an opaque exception out.

    A missing or broken field adapter means provenance and canonicalization cannot
    be proven.  Treat that as protection unavailable before the MCP service has a
    chance to serialize a value, rather than returning a generic tool failure.
    """

    try:
        field_type = field.get_type()
        field_type_name = field_type.type
    except Exception as exc:  # adapter failures are intentionally fail-closed
        raise protection_unavailable() from exc
    if not isinstance(field_type_name, str) or not field_type_name:
        raise protection_unavailable()
    return field_type_name


def verify_policy_snapshot(
    endpoint: MCPEndpoint, snapshot: MCPProtectionPolicyState, *, lock: bool
) -> None:
    """Fail closed unless the stored policy still matches ``snapshot``.

    ``lock=True`` also takes a row lock on the policy, keeping its identity
    stable through a mutation and the response masking inside the caller's
    transaction.  ``lock=False`` re-checks it after mask tokens were issued.
    """

    queryset = MCPProtectionPolicy.objects
    if lock:
        queryset = queryset.select_for_update()
    try:
        current = queryset.get(
            id=snapshot.policy_id,
            endpoint=endpoint,
            revision=snapshot.revision,
            access_generation=snapshot.access_generation,
            lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
            safe_reason_code=MCPProtectionSafeReason.NONE,
        )
    except MCPProtectionPolicy.DoesNotExist:
        raise protection_unavailable()
    active_ids = set(
        current.protected_fields.filter(
            state=MCPProtectedFieldState.ACTIVE
        ).values_list("field_id", flat=True)
    )
    if active_ids != {field.field_id for field in snapshot.protected_fields}:
        raise protection_unavailable()


class ProtectedOutputField:
    """A protected binding that leaves a table, with its operation class."""

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


def table_has_protected_output(
    table_id: int, protected_fields, workspace_id: int
) -> bool:
    """Return whether direct or transitive protected data can leave this table."""

    return bool(protected_output_fields(table_id, protected_fields, workspace_id))


def protected_output_fields(
    table_id: int, protected_fields, workspace_id: int
) -> tuple[ProtectedOutputField, ...]:
    """Include derived fields whose dependency graph contains a protected leaf."""

    direct_fields = tuple(
        field for field in protected_fields if field.table_id == table_id
    )
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
            raise protection_unavailable()
        if field_id in visited:
            return
        visiting.add(field_id)
        for dependency_id in dependencies.get(field_id, ()):
            if dependency_id in affected_ids:
                visit(dependency_id)
            elif dependency_id not in known_field_ids:
                # A dependency that disappeared from the active field graph
                # cannot be proven public or protected.
                raise protection_unavailable()
        visiting.remove(field_id)
        visited.add(field_id)

    for field_id in affected_ids:
        visit(field_id)
    # A broken reference is only relevant when it belongs to a protected leaf
    # or to a derived field whose value is transitively protected.  An unrelated
    # broken formula elsewhere in the workspace must not make every protected
    # table unreadable; the affected field itself remains fail-closed.
    if broken_dependant_ids & (protected_ids | derived_ids):
        raise protection_unavailable()
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
                    field_type=safe_field_type_name(field),
                )
            )
    return tuple(
        ProtectedOutputField(
            binding=field,
            operation_class="preserve_cell"
            if field.field_id in direct_by_id
            else "display_only",
        )
        for field in output_fields
    )
