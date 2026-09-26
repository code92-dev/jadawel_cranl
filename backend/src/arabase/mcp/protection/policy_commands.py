"""Idempotent MCP protection policy commands.

Creating an endpoint with its initial policy, replacing or reactivating a policy,
and the ownerless admin delete. Lifecycle audit writers live in ``lifecycle``,
which never imports this module.
"""

import hashlib
import json
import re
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from rest_framework.exceptions import PermissionDenied, ValidationError

from arabase.mcp.protection.lifecycle import (
    record_mcp_protection_lifecycle_transition,
    record_policy_became_nonempty,
)
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionCommand,
    MCPProtectionEditCommand,
    MCPProtectionLifecycleAudit,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from arabase.mcp.protection.readiness import (
    ensure_policy_admission_allowed,
    ensure_protection_vault_ready,
)
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.operations import ReadFieldOperationType
from jadawel.core.action.registries import action_type_registry
from jadawel.core.handler import CoreHandler
from jadawel.core.mcp.actions import CreateMCPEndpointActionType
from jadawel.core.mcp.exceptions import MCPEndpointDoesNotExist
from jadawel.core.mcp.handler import MCPEndpointHandler
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.models import WORKSPACE_USER_PERMISSION_ADMIN, WorkspaceUser

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class MCPProtectionPolicyConflict(Exception):
    """The editor submitted a stale policy revision."""


class MCPProtectionPolicyNotReady(Exception):
    """The endpoint cannot be safely reactivated yet."""


@dataclass(frozen=True, slots=True)
class CompositeEndpointCreationResult:
    endpoint: MCPEndpoint
    replayed: bool


@dataclass(frozen=True, slots=True)
class MCPProtectionPolicyEditResult:
    policy: MCPProtectionPolicy
    replayed: bool = False


def validate_idempotency_key(value: str | None) -> str:
    if value is None or IDEMPOTENCY_KEY_PATTERN.fullmatch(value) is None:
        raise ValidationError(
            {"idempotency_key": "Provide an 8 to 128 character Idempotency-Key."}
        )
    return value


def _request_fingerprint(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _reject_key_reuse(stored_fingerprint: str, fingerprint: str) -> None:
    if stored_fingerprint != fingerprint:
        raise ValidationError(
            {"idempotency_key": "This key was already used for another request."}
        )


def load_and_validate_protected_fields(
    user, workspace, field_ids: list[int]
) -> list[Field]:
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
        {
            "confirm_empty_policy": confirm_empty_policy,
            "name": name,
            "protected_field_ids": sorted(protected_field_ids),
            "workspace_id": workspace_id,
        }
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
        _reject_key_reuse(existing.request_fingerprint, fingerprint)
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
        _reject_key_reuse(existing.request_fingerprint, fingerprint)
        return CompositeEndpointCreationResult(existing.endpoint, replayed=True)

    workspace = CoreHandler().get_workspace(workspace_id)
    fields = load_and_validate_protected_fields(user, workspace, protected_field_ids)
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


def replace_mcp_protection_policy(
    *,
    user,
    endpoint_id: int,
    protected_field_ids: list[int],
    expected_revision: int,
    confirm_remove_field_ids: list[int],
    idempotency_key: str,
) -> MCPProtectionPolicyEditResult:
    if len(protected_field_ids) != len(set(protected_field_ids)):
        raise ValidationError({"protected_field_ids": "Field IDs must be unique."})
    if len(confirm_remove_field_ids) != len(set(confirm_remove_field_ids)):
        raise ValidationError({"confirm_remove_field_ids": "Field IDs must be unique."})
    fingerprint = _request_fingerprint(
        {
            "confirm_remove_field_ids": sorted(confirm_remove_field_ids),
            "endpoint_id": endpoint_id,
            "expected_revision": expected_revision,
            "protected_field_ids": sorted(protected_field_ids),
        }
    )
    try:
        return _replace_mcp_protection_policy(
            user=user,
            endpoint_id=endpoint_id,
            protected_field_ids=protected_field_ids,
            expected_revision=expected_revision,
            confirm_remove_field_ids=confirm_remove_field_ids,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )
    except IntegrityError:
        command = (
            MCPProtectionEditCommand.objects.select_related("policy")
            .filter(actor=user, idempotency_key=idempotency_key)
            .first()
        )
        if command is None:
            raise
        _reject_key_reuse(command.request_fingerprint, fingerprint)
        return MCPProtectionPolicyEditResult(command.policy, replayed=True)


@transaction.atomic
def _replace_mcp_protection_policy(
    *,
    user,
    endpoint_id: int,
    protected_field_ids: list[int],
    expected_revision: int,
    confirm_remove_field_ids: list[int],
    idempotency_key: str,
    fingerprint: str,
) -> MCPProtectionPolicyEditResult:
    endpoint = MCPEndpointHandler().get_endpoint(user, endpoint_id)
    policy = MCPProtectionPolicy.objects.select_for_update().get(endpoint=endpoint)
    existing_command = (
        MCPProtectionEditCommand.objects.select_for_update()
        .select_related("policy")
        .filter(actor=user, idempotency_key=idempotency_key)
        .first()
    )
    if existing_command is not None:
        _reject_key_reuse(existing_command.request_fingerprint, fingerprint)
        return MCPProtectionPolicyEditResult(existing_command.policy, replayed=True)
    if policy.revision != expected_revision:
        raise MCPProtectionPolicyConflict

    fields = load_and_validate_protected_fields(
        user, endpoint.workspace, protected_field_ids
    )
    current_ids = set(
        MCPProtectedField.objects.filter(policy=policy).values_list(
            "field_id", flat=True
        )
    )
    requested_ids = set(protected_field_ids)
    if requested_ids or current_ids:
        ensure_policy_admission_allowed(user)
    if requested_ids - current_ids:
        ensure_protection_vault_ready()
    removed_ids = current_ids - requested_ids
    if removed_ids and set(confirm_remove_field_ids) != removed_ids:
        raise ValidationError(
            {
                "confirm_remove_field_ids": (
                    "Confirm every field being removed from the protection policy."
                )
            }
        )
    if set(confirm_remove_field_ids) - removed_ids:
        raise ValidationError(
            {"confirm_remove_field_ids": "Only removed fields may be confirmed."}
        )

    if requested_ids != current_ids:
        MCPProtectedField.objects.filter(policy=policy).delete()
        MCPProtectedField.objects.bulk_create(
            [MCPProtectedField(policy=policy, field=field) for field in fields]
        )
        policy.revision += 1
        policy.access_generation += 1
        policy.save(update_fields=["revision", "access_generation", "updated_on"])
        if not current_ids and requested_ids:
            record_policy_became_nonempty(policy=policy, actor=user)
    MCPProtectionEditCommand.objects.create(
        actor=user,
        policy=policy,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        resulting_revision=policy.revision,
    )
    policy.refresh_from_db()
    return MCPProtectionPolicyEditResult(policy)


@transaction.atomic
def reactivate_mcp_protection_policy(
    *, user, endpoint_id: int, expected_revision: int
) -> MCPProtectionPolicy:
    """Revalidate a suspended policy and issue a fresh endpoint credential."""

    endpoint = MCPEndpointHandler().get_endpoint(user, endpoint_id)
    policy = MCPProtectionPolicy.objects.select_for_update().get(endpoint=endpoint)
    if policy.revision != expected_revision:
        raise MCPProtectionPolicyConflict
    if policy.lifecycle_status == MCPProtectionLifecycleStatus.ACTIVE:
        return policy
    if not user.is_active or (
        getattr(user, "profile", None) and user.profile.to_be_deleted
    ):
        raise MCPProtectionPolicyNotReady
    if (
        endpoint.workspace.trashed
        or not WorkspaceUser.objects.filter(
            user=user, workspace=endpoint.workspace
        ).exists()
    ):
        raise MCPProtectionPolicyNotReady

    fields = list(policy.protected_fields.values_list("field_id", flat=True))
    try:
        load_and_validate_protected_fields(user, endpoint.workspace, fields)
    except ValidationError as exc:
        raise MCPProtectionPolicyNotReady from exc

    endpoint.key = MCPEndpointHandler().generate_unique_key()
    endpoint.save(update_fields=["key"])
    MCPProtectedField.objects.filter(policy=policy).update(
        state=MCPProtectedFieldState.ACTIVE,
        safe_reason_code=MCPProtectionSafeReason.NONE,
    )
    policy.refresh_from_db()
    previous_status = policy.lifecycle_status
    policy.lifecycle_status = MCPProtectionLifecycleStatus.ACTIVE
    policy.safe_reason_code = MCPProtectionSafeReason.NONE
    policy.revision += 1
    policy.access_generation += 1
    policy.save(
        update_fields=[
            "lifecycle_status",
            "safe_reason_code",
            "revision",
            "access_generation",
            "updated_on",
        ]
    )
    record_mcp_protection_lifecycle_transition(
        policy=policy,
        from_lifecycle_status=previous_status,
        to_lifecycle_status=policy.lifecycle_status,
        reason_code=MCPProtectionSafeReason.NONE,
        actor=user,
        metadata={"trigger": "owner_reactivation"},
    )
    return policy


@transaction.atomic
def delete_ownerless_suspended_endpoint(*, user, endpoint_id: int) -> None:
    """Let a workspace admin remove only an endpoint with no viable owner.

    The owner-only core MCP delete path remains unchanged.  This additive path is
    intentionally narrower: an admin must be an active workspace administrator,
    the endpoint must be suspended or protection-blocked, and the original owner
    must no longer be an active workspace member/account.  The audit is written
    before deletion and survives through its nullable endpoint foreign key.
    """

    try:
        endpoint = (
            MCPEndpoint.objects.select_for_update(of=("self",))
            .select_related("workspace", "user__profile", "arabase_protection_policy")
            .get(id=endpoint_id)
        )
    except MCPEndpoint.DoesNotExist as exc:
        raise MCPEndpointDoesNotExist from exc

    if not getattr(user, "is_authenticated", False) or not user.is_active:
        raise PermissionDenied(
            "Only an active workspace administrator may delete this endpoint."
        )
    if (
        endpoint.workspace.trashed
        or not WorkspaceUser.objects.filter(
            user_id=user.id,
            workspace_id=endpoint.workspace_id,
            permissions=WORKSPACE_USER_PERMISSION_ADMIN,
        ).exists()
    ):
        raise PermissionDenied(
            "Only a workspace administrator may delete this endpoint."
        )

    policy = endpoint.arabase_protection_policy
    if policy.lifecycle_status not in (
        MCPProtectionLifecycleStatus.SUSPENDED,
        MCPProtectionLifecycleStatus.PROTECTION_BLOCKED,
    ):
        raise PermissionDenied(
            "Only a suspended or blocked ownerless endpoint may be deleted."
        )

    owner_active_member = (
        endpoint.user is not None
        and endpoint.user.is_active
        and not getattr(getattr(endpoint.user, "profile", None), "to_be_deleted", False)
        and WorkspaceUser.objects.filter(
            user_id=endpoint.user_id,
            workspace_id=endpoint.workspace_id,
        ).exists()
    )
    if owner_active_member:
        raise PermissionDenied(
            "The endpoint owner must be inactive or absent from the workspace."
        )

    MCPProtectionLifecycleAudit.objects.create(
        endpoint=endpoint,
        actor=user,
        event_type="ownerless_admin_delete",
        from_lifecycle_status=policy.lifecycle_status,
        to_lifecycle_status="deleted",
        reason_code=policy.safe_reason_code,
        policy_revision=policy.revision,
        access_generation=policy.access_generation,
        metadata={"endpoint_id": endpoint.id},
    )
    endpoint.delete()
