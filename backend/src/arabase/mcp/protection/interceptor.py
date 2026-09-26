from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from arabase.mcp.protection import limits
from arabase.mcp.protection.audit import content_blind_mcp_mutation
from arabase.mcp.protection.egress import mask_table_rows
from arabase.mcp.protection.policy_state import (
    get_mcp_protection_policy_state,
    protection_unavailable,
    table_has_protected_output,
    verify_policy_snapshot,
)
from arabase.mcp.protection.tokens import (
    contains_mask_token_marker,
    extract_mask_token_handle,
)
from arabase.mcp.protection.vault import (
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    get_mask_token_vault,
)
from jadawel.contrib.database.api.rows.serializers import serialize_rows_for_response
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.mcp import services
from jadawel.core.mcp.errors import SafeMCPToolError
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.mcp.registries import MCPTool


class MCPToolContract(StrEnum):
    """How the protection boundary treats one MCP tool's call."""

    # Returns only schema metadata or a mutation receipt, never cell values.
    METADATA = "metadata"
    # A page tool that owns its artifact draft, approval and runtime checks.
    PAGE_ARTIFACT = "page_artifact"
    # Reads or writes row values, so protected cells are masked or redeemed.
    PROTECTED_ROWS = "protected_rows"


MCP_TOOL_PROTECTION_CONTRACTS = {
    "list_databases": MCPToolContract.METADATA,
    "create_database": MCPToolContract.METADATA,
    "list_tables": MCPToolContract.METADATA,
    "create_table": MCPToolContract.METADATA,
    "update_table": MCPToolContract.METADATA,
    "delete_table": MCPToolContract.METADATA,
    "get_table_schema": MCPToolContract.METADATA,
    "create_fields": MCPToolContract.METADATA,
    "update_fields": MCPToolContract.METADATA,
    "delete_fields": MCPToolContract.METADATA,
    "list_table_rows": MCPToolContract.PROTECTED_ROWS,
    "create_rows": MCPToolContract.PROTECTED_ROWS,
    "update_rows": MCPToolContract.PROTECTED_ROWS,
    "delete_rows": MCPToolContract.METADATA,
    "list_page_views": MCPToolContract.METADATA,
    "get_page_view": MCPToolContract.PAGE_ARTIFACT,
    "create_page_view": MCPToolContract.PAGE_ARTIFACT,
    "update_page_view": MCPToolContract.PAGE_ARTIFACT,
    "list_page_view_revisions": MCPToolContract.PAGE_ARTIFACT,
    "restore_page_view_revision": MCPToolContract.PAGE_ARTIFACT,
}


def get_mcp_tool_protection_contract(tool_name: str) -> MCPToolContract:
    try:
        return MCP_TOOL_PROTECTION_CONTRACTS[tool_name]
    except KeyError as exc:
        raise ImproperlyConfigured(
            f"MCP tool '{tool_name}' has no protection contract."
        ) from exc


def validate_mcp_tool_protection_contracts(tools: Iterable[MCPTool]) -> None:
    for tool in tools:
        if tool.__class__.call is not MCPTool.call:
            raise ImproperlyConfigured(
                f"MCP tool '{tool.type}' bypasses the protected call boundary."
            )
        get_mcp_tool_protection_contract(tool.type)


def intercept_mcp_tool_call(
    endpoint: MCPEndpoint,
    tool: MCPTool,
    args: Any,
    execute: Callable[[], Any],
) -> Any:
    """Apply the declared MCP contract before executing a validated tool call."""

    # Load the durable policy before resolving the contract.  An unprotected
    # endpoint must remain compatible with an additive tool that has not yet
    # opted into the inventory, while a non-empty policy must fail closed with
    # the same fixed protection error rather than leaking a configuration
    # traceback.
    policy = get_mcp_protection_policy_state(endpoint)
    if tool.type == "create_rows":
        # The reserved envelope is never an ordinary user value, even for an
        # endpoint whose policy is currently empty.
        _reject_token_envelopes(args.rows)
    # A mask envelope is an authority-bearing handle, never an ordinary cell
    # value.  Reject it even when the policy is empty or the target table is
    # outside the protected set.  The only supported update path is a
    # same-cell redemption on a table with a direct protected field, which is
    # validated below.
    if (
        tool.type == "update_rows"
        and any(contains_mask_token_marker(row.__pydantic_extra__) for row in args.rows)
        and (
            not policy.has_protected_fields
            or not any(
                field.table_id == args.table_id for field in policy.protected_fields
            )
        )
    ):
        raise protection_unavailable()
    if not policy.has_protected_fields:
        return execute()
    try:
        contract = get_mcp_tool_protection_contract(tool.type)
    except ImproperlyConfigured as exc:
        raise protection_unavailable() from exc
    # Metadata tools never return cell values.  Page tools own their artifact
    # draft/approval and runtime projection checks; they must not be treated as
    # ordinary row tools, which would reject every protected page call before
    # the service can return safe metadata or create a draft.
    if contract is not MCPToolContract.PROTECTED_ROWS:
        return execute()
    if tool.type == "list_table_rows" and not table_has_protected_output(
        args.table_id, policy.protected_fields, endpoint.workspace_id
    ):
        return execute()
    if tool.type != "list_table_rows" and not any(
        field.table_id == args.table_id for field in policy.protected_fields
    ):
        return execute()
    if tool.type == "list_table_rows" and args.size > limits.MAX_ROWS_PER_CALL:
        raise protection_unavailable()
    if (
        tool.type in ("create_rows", "update_rows")
        and len(args.rows) > limits.MAX_ROWS_PER_CALL
    ):
        raise protection_unavailable()
    if tool.type == "list_table_rows" and getattr(args, "search", ""):
        raise protection_unavailable()

    with transaction.atomic():
        # Keep policy identity stable through the mutation and response masking.
        verify_policy_snapshot(endpoint, policy, lock=True)
        restore = None
        try:
            if tool.type == "update_rows":
                restore = _prepare_update_for_protected_cells(endpoint, args, policy)
            if tool.type in ("create_rows", "update_rows"):
                with content_blind_mcp_mutation(
                    endpoint=endpoint,
                    tool_type=tool.type,
                    table_id=args.table_id,
                    row_count=len(args.rows),
                    policy_revision=policy.revision,
                    access_generation=policy.access_generation,
                    protected_field_ids=tuple(
                        field.field_id
                        for field in policy.protected_fields
                        if field.table_id == args.table_id
                    ),
                ):
                    result = execute()
            else:
                result = execute()
            return mask_table_rows(endpoint, args.table_id, result, policy)
        finally:
            if restore is not None:
                restore()


def _reject_token_envelopes(value: Any) -> None:
    """Reject handles on create and in every non-redemption input position."""

    if contains_mask_token_marker(value):
        raise protection_unavailable()


def _prepare_update_for_protected_cells(endpoint, args, policy):
    """Validate and temporarily redeem same-cell tokens for one whole batch."""

    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    model = table.get_model()
    fields = {
        field.field_name: field
        for field in policy.protected_fields
        if field.table_id == args.table_id
    }
    row_ids = [row.id for row in args.rows]
    if len(set(row_ids)) != len(row_ids):
        raise protection_unavailable()
    locked_rows = model.objects.select_for_update().filter(id__in=row_ids)
    locked_by_id = {row.id: row for row in locked_rows}
    if len(locked_by_id) != len(row_ids):
        raise protection_unavailable()
    serialized_rows = serialize_rows_for_response(
        list(locked_by_id.values()), model, user_field_names=True
    )
    serialized_by_id = {row["id"]: row for row in serialized_rows}
    protected_field_models = {
        field.id: field
        for field in Field.objects.filter(
            id__in=[field.field_id for field in fields.values()],
            table_id=args.table_id,
            trashed=False,
        )
    }
    vault = None
    # The upstream row service treats omitted values as field defaults (for
    # example, an omitted text value becomes ``""``).  That is correct for a
    # normal REST update, but it would silently clear a protected cell.  Add
    # the current internal value for every omitted writable protected field so
    # the downstream update has explicit preserve semantics.  Keep track of
    # those temporary values and remove them before the validated Pydantic
    # object can escape this boundary.
    originals = []
    redeemed_count = 0
    try:
        for spec in args.rows:
            extras = spec.__pydantic_extra__
            observed_row = locked_by_id[spec.id]
            for name, protected_field in fields.items():
                if name in extras:
                    continue
                protected_field_model = protected_field_models.get(
                    protected_field.field_id
                )
                if protected_field_model is None:
                    raise protection_unavailable()
                value = _field_value(protected_field_model, observed_row)
                # Derived/read-only fields are recomputed by the row service
                # and must not be sent back as write inputs.
                if value is _READ_ONLY:
                    continue
                extras[name] = value
                originals.append((spec, name, None, True))
            for name, value in list(extras.items()):
                protected_field = fields.get(name)
                has_marker = contains_mask_token_marker(value)
                if not has_marker:
                    continue
                if protected_field is None:
                    raise protection_unavailable()
                protected_field_model = protected_field_models.get(
                    protected_field.field_id
                )
                if protected_field_model is None:
                    raise protection_unavailable()
                handle = extract_mask_token_handle(value)
                if handle is None:
                    raise protection_unavailable()
                current = serialized_by_id[spec.id]
                if name not in current:
                    raise protection_unavailable()
                vault = vault or get_mask_token_vault()
                valid = vault.redeem(
                    handle,
                    MaskTokenBinding(
                        endpoint_id=endpoint.id,
                        workspace_id=endpoint.workspace_id,
                        table_id=args.table_id,
                        row_id=spec.id,
                        field_id=protected_field.field_id,
                        policy_revision=policy.revision,
                        access_generation=policy.access_generation,
                        operation_class="preserve_cell",
                        observed_row_state=observed_row.updated_on.isoformat(),
                        field_type=protected_field.field_type,
                    ),
                    current[name],
                )
                if not valid:
                    raise protection_unavailable()
                redeemed_count += 1
                if redeemed_count > limits.MAX_ISSUED_OR_REDEEMED_PER_CALL:
                    raise protection_unavailable()
                originals.append((spec, name, value, False))
                # The response serializer may intentionally expose a richer
                # shape than the row write serializer (for example, a
                # single-select response is an option object while updates
                # accept the option id).  Use the field adapter's internal
                # value so same-cell redemption preserves every writable field
                # type without forwarding response-only structures.
                internal_value = _field_value(protected_field_model, observed_row)
                if internal_value is _READ_ONLY:
                    raise protection_unavailable()
                spec.__pydantic_extra__[name] = internal_value
    except MaskTokenVaultUnavailable:
        raise protection_unavailable()

    def restore() -> None:
        for spec, name, value, was_missing in originals:
            if was_missing:
                spec.__pydantic_extra__.pop(name, None)
            else:
                spec.__pydantic_extra__[name] = value

    return restore


_READ_ONLY = object()


def _field_value(field_model, row):
    """Return the writable internal value of one cell, or ``_READ_ONLY``."""

    try:
        field_type = field_model.get_type()
        if field_type.read_only:
            return _READ_ONLY
        return field_type.get_internal_value_from_db(row, field_model.db_column)
    except SafeMCPToolError:
        raise
    except Exception as exc:
        raise protection_unavailable() from exc
