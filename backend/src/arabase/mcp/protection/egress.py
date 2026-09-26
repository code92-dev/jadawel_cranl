import json
from copy import deepcopy
from typing import Any

from arabase.mcp.protection import limits
from arabase.mcp.protection.policy_state import (
    MCPProtectionPolicyState,
    protected_output_fields,
    protection_unavailable,
    verify_policy_snapshot,
)
from arabase.mcp.protection.vault import (
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    get_mask_token_vault,
)
from jadawel.contrib.database.table.models import Table
from jadawel.core.mcp.errors import SafeMCPToolError
from jadawel.core.mcp.models import MCPEndpoint


def mask_table_rows(
    endpoint: MCPEndpoint,
    table_id: int,
    result: Any,
    policy: MCPProtectionPolicyState,
) -> Any:
    """Replace direct protected cells with fresh same-cell mask tokens."""

    if not policy.protected_fields:
        return result
    table = Table.objects.get(id=table_id, database__workspace_id=endpoint.workspace_id)
    fields = protected_output_fields(
        table_id, policy.protected_fields, endpoint.workspace_id
    )
    if not fields:
        return result

    output = deepcopy(result)
    rows = output["results"] if isinstance(output, dict) else output
    if not isinstance(rows, list):
        raise protection_unavailable()
    if len(rows) > limits.MAX_ROWS_PER_CALL:
        raise protection_unavailable()

    model = table.get_model()
    row_ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != len(rows) or any(row_id is None for row_id in row_ids):
        raise protection_unavailable()
    observed_rows = model.objects.in_bulk(row_ids)
    if len(observed_rows) != len(row_ids):
        raise protection_unavailable()
    non_empty_values = 0
    for row in rows:
        for field in fields:
            if field.field_name not in row:
                raise protection_unavailable()
            if not _is_empty_value(row[field.field_name]):
                non_empty_values += 1
    if non_empty_values > limits.MAX_ISSUED_OR_REDEEMED_PER_CALL:
        raise protection_unavailable()

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
        verify_policy_snapshot(endpoint, policy, lock=False)
        if (
            len(
                json.dumps(
                    output,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode()
            )
            > limits.MAX_RESPONSE_BYTES
        ):
            raise protection_unavailable()
    except (MaskTokenVaultUnavailable, SafeMCPToolError):
        if vault is not None:
            vault.delete(issued_digests)
        raise protection_unavailable()
    return output


def _is_empty_value(value: Any) -> bool:
    return (
        value is None
        or value == ""
        or (isinstance(value, (list, dict, tuple)) and len(value) == 0)
    )
