import hashlib
import json
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from rest_framework.exceptions import ValidationError

from arabase.mcp.protection.admission import (
    ensure_policy_admission_allowed,
    ensure_protection_vault_ready,
)
from arabase.mcp.protection.creation import _load_and_validate_fields
from arabase.mcp.protection.lifecycle import (
    record_mcp_protection_lifecycle_transition,
    record_policy_became_nonempty,
)
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionEditCommand,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from jadawel.core.mcp.handler import MCPEndpointHandler
from jadawel.core.models import WorkspaceUser


class MCPProtectionPolicyConflict(Exception):
    """The editor submitted a stale policy revision."""


class MCPProtectionPolicyNotReady(Exception):
    """The endpoint cannot be safely reactivated yet."""


@dataclass(frozen=True, slots=True)
class MCPProtectionPolicyEditResult:
    policy: MCPProtectionPolicy
    replayed: bool = False


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
        endpoint_id,
        protected_field_ids,
        expected_revision,
        confirm_remove_field_ids,
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
        if command.request_fingerprint != fingerprint:
            raise ValidationError(
                {"idempotency_key": "This key was already used for another request."}
            )
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
        if existing_command.request_fingerprint != fingerprint:
            raise ValidationError(
                {"idempotency_key": "This key was already used for another request."}
            )
        return MCPProtectionPolicyEditResult(existing_command.policy, replayed=True)
    if policy.revision != expected_revision:
        raise MCPProtectionPolicyConflict

    fields = _load_and_validate_fields(user, endpoint.workspace, protected_field_ids)
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
        _load_and_validate_fields(user, endpoint.workspace, fields)
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


def _request_fingerprint(
    endpoint_id: int,
    protected_field_ids: list[int],
    expected_revision: int,
    confirm_remove_field_ids: list[int],
) -> str:
    payload = json.dumps(
        {
            "confirm_remove_field_ids": sorted(confirm_remove_field_ids),
            "endpoint_id": endpoint_id,
            "expected_revision": expected_revision,
            "protected_field_ids": sorted(protected_field_ids),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
