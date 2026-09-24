import hashlib
import json
import re
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from rest_framework.exceptions import ValidationError

from arabase.mcp.protection.admission import (
    ensure_policy_admission_allowed,
    ensure_protection_vault_ready,
)
from arabase.mcp.protection.lifecycle import record_policy_became_nonempty
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectionCommand,
    MCPProtectionPolicy,
)
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.operations import ReadFieldOperationType
from jadawel.core.action.registries import action_type_registry
from jadawel.core.handler import CoreHandler
from jadawel.core.mcp.actions import CreateMCPEndpointActionType
from jadawel.core.mcp.models import MCPEndpoint

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


@dataclass(frozen=True, slots=True)
class CompositeEndpointCreationResult:
    endpoint: MCPEndpoint
    replayed: bool


def validate_idempotency_key(value: str | None) -> str:
    if value is None or IDEMPOTENCY_KEY_PATTERN.fullmatch(value) is None:
        raise ValidationError(
            {"idempotency_key": "Provide an 8 to 128 character Idempotency-Key."}
        )
    return value


def create_protected_mcp_endpoint(
    *,
    user,
    name: str,
    workspace_id: int,
    protected_field_ids: list[int],
    confirm_empty_policy: bool,
    idempotency_key: str,
) -> CompositeEndpointCreationResult:
    """Create an endpoint and its exact initial policy as one command."""

    if not protected_field_ids and not confirm_empty_policy:
        raise ValidationError(
            {"confirm_empty_policy": "Confirm an endpoint with no protected fields."}
        )
    if protected_field_ids:
        ensure_policy_admission_allowed(user)
        ensure_protection_vault_ready()

    fingerprint = _request_fingerprint(
        name, workspace_id, protected_field_ids, confirm_empty_policy
    )
    try:
        return _create_protected_mcp_endpoint(
            user=user,
            name=name,
            workspace_id=workspace_id,
            protected_field_ids=protected_field_ids,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )
    except IntegrityError:
        # Two workers may observe an unused key concurrently. The unique command
        # constraint rolls the losing endpoint transaction back; its caller then
        # replays the winner instead of leaking a second credential.
        existing = (
            MCPProtectionCommand.objects.select_related("endpoint__workspace")
            .filter(actor=user, idempotency_key=idempotency_key)
            .first()
        )
        if existing is None:
            raise
        if existing.request_fingerprint != fingerprint:
            raise ValidationError(
                {"idempotency_key": "This key was already used for another request."}
            )
        return CompositeEndpointCreationResult(existing.endpoint, replayed=True)


@transaction.atomic
def _create_protected_mcp_endpoint(
    *,
    user,
    name: str,
    workspace_id: int,
    protected_field_ids: list[int],
    idempotency_key: str,
    fingerprint: str,
) -> CompositeEndpointCreationResult:
    existing = (
        MCPProtectionCommand.objects.select_for_update()
        .select_related("endpoint__workspace")
        .filter(actor=user, idempotency_key=idempotency_key)
        .first()
    )
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise ValidationError(
                {"idempotency_key": "This key was already used for another request."}
            )
        return CompositeEndpointCreationResult(existing.endpoint, replayed=True)

    workspace = CoreHandler().get_workspace(workspace_id)
    fields = _load_and_validate_fields(user, workspace, protected_field_ids)
    if MCPEndpoint.objects.filter(user=user, workspace=workspace, name=name).exists():
        raise ValidationError(
            {"name": "An MCP endpoint with this name already exists in the workspace."}
        )

    endpoint = action_type_registry.get(CreateMCPEndpointActionType.type).do(
        user, workspace, name
    )
    policy = MCPProtectionPolicy.objects.select_for_update().get(endpoint=endpoint)
    MCPProtectedField.objects.bulk_create(
        [MCPProtectedField(policy=policy, field=field) for field in fields]
    )
    if fields:
        record_policy_became_nonempty(policy=policy, actor=user)
    MCPProtectionCommand.objects.create(
        actor=user,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        endpoint=endpoint,
    )
    return CompositeEndpointCreationResult(endpoint, replayed=False)


def _load_and_validate_fields(user, workspace, field_ids: list[int]) -> list[Field]:
    if len(field_ids) != len(set(field_ids)):
        raise ValidationError({"protected_field_ids": "Field IDs must be unique."})
    fields = list(
        Field.objects.filter(
            id__in=field_ids,
            table__database__workspace=workspace,
            trashed=False,
            table__trashed=False,
            table__database__trashed=False,
        )
        .select_related("table__database__workspace")
        .order_by("id")
    )
    if len(fields) != len(field_ids):
        raise ValidationError(
            {"protected_field_ids": "Select active fields from the endpoint workspace."}
        )
    for field in fields:
        CoreHandler().check_permissions(
            user,
            ReadFieldOperationType.type,
            workspace=workspace,
            context=field,
        )
        field.get_type()
    return fields


def _request_fingerprint(
    name: str,
    workspace_id: int,
    field_ids: list[int],
    confirm_empty_policy: bool,
) -> str:
    payload = json.dumps(
        {
            "confirm_empty_policy": confirm_empty_policy,
            "name": name,
            "protected_field_ids": sorted(field_ids),
            "workspace_id": workspace_id,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
