from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleAudit,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
    MCPProtectionSafeReason,
)
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.registries import field_type_registry
from jadawel.contrib.database.models import Database
from jadawel.contrib.database.table.models import Table
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.models import (
    UserProfile,
    Workspace,
    WorkspaceUser,
)


def create_empty_mcp_protection_policy(
    sender, instance: MCPEndpoint, created: bool, **kwargs
) -> None:
    if created:
        MCPProtectionPolicy.objects.create(endpoint=instance)


def record_mcp_protection_lifecycle_transition(
    *,
    policy: MCPProtectionPolicy,
    from_lifecycle_status: str,
    to_lifecycle_status: str,
    reason_code: str = "",
    event_type: str = "lifecycle_transition",
    actor=None,
    metadata: dict | None = None,
) -> None:
    """Write a content-blind lifecycle transition audit entry."""

    if from_lifecycle_status == to_lifecycle_status and not reason_code:
        return
    MCPProtectionLifecycleAudit.objects.create(
        endpoint_id=policy.endpoint_id,
        actor=actor,
        event_type=event_type,
        from_lifecycle_status=from_lifecycle_status,
        to_lifecycle_status=to_lifecycle_status,
        reason_code=reason_code,
        policy_revision=policy.revision,
        access_generation=policy.access_generation,
        metadata=metadata or {},
    )


def record_policy_became_nonempty(*, policy: MCPProtectionPolicy, actor=None) -> None:
    """Persist the forward-only rollout boundary for first protected admission."""

    MCPProtectionLifecycleAudit.objects.create(
        endpoint_id=policy.endpoint_id,
        actor=actor,
        event_type="POLICY_BECAME_NONEMPTY",
        from_lifecycle_status=policy.lifecycle_status,
        to_lifecycle_status=policy.lifecycle_status,
        reason_code=MCPProtectionSafeReason.NONE,
        policy_revision=policy.revision,
        access_generation=policy.access_generation,
        metadata={"protected_field_count": policy.protected_fields.count()},
    )


def _bump_policies(endpoint_ids, *, reason=None, lifecycle_status=None):
    endpoint_ids = list(set(endpoint_ids))
    before = {
        row["endpoint_id"]: row
        for row in MCPProtectionPolicy.objects.filter(
            endpoint_id__in=endpoint_ids
        ).values(
            "endpoint_id",
            "revision",
            "access_generation",
            "lifecycle_status",
            "safe_reason_code",
        )
    }
    updates = {
        "revision": F("revision") + 1,
        "access_generation": F("access_generation") + 1,
    }
    if reason is not None:
        updates["safe_reason_code"] = reason
    if lifecycle_status is not None:
        updates["lifecycle_status"] = lifecycle_status
    MCPProtectionPolicy.objects.filter(endpoint_id__in=endpoint_ids).update(**updates)
    if reason is None and lifecycle_status is None:
        return
    target_status = lifecycle_status
    target_reason = reason
    audits = []
    for row in before.values():
        if row["lifecycle_status"] == (
            target_status or row["lifecycle_status"]
        ) and row["safe_reason_code"] == (target_reason or row["safe_reason_code"]):
            continue
        audits.append(
            MCPProtectionLifecycleAudit(
                endpoint_id=row["endpoint_id"],
                event_type="lifecycle_transition",
                from_lifecycle_status=row["lifecycle_status"],
                to_lifecycle_status=target_status or row["lifecycle_status"],
                reason_code=target_reason or row["safe_reason_code"],
                policy_revision=row["revision"] + 1,
                access_generation=row["access_generation"] + 1,
                metadata={},
            )
        )
    if audits:
        MCPProtectionLifecycleAudit.objects.bulk_create(audits)


def _suspend_workspace_policies(workspace_id: int, suspended: bool) -> None:
    # ``MCPEndpoint.objects`` inherits the parent-workspace trash filter and
    # therefore returns no endpoints after the workspace has just been marked
    # trashed.  Lifecycle suspension must still reach those endpoints, so use
    # the all-rows manager while the parent is transitioning.
    endpoint_ids = MCPEndpoint.objects_and_trash.filter(
        workspace_id=workspace_id
    ).values_list("id", flat=True)
    if suspended:
        _bump_policies(
            endpoint_ids,
            reason=MCPProtectionSafeReason.WORKSPACE_SUSPENDED,
            lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        )
    else:
        policies = list(
            MCPProtectionPolicy.objects.filter(
                endpoint_id__in=endpoint_ids,
                lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
                safe_reason_code=MCPProtectionSafeReason.WORKSPACE_SUSPENDED,
            )
        )
        MCPProtectionPolicy.objects.filter(
            id__in=[policy.id for policy in policies]
        ).update(
            revision=F("revision") + 1,
            access_generation=F("access_generation") + 1,
            lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
            safe_reason_code=MCPProtectionSafeReason.NONE,
        )
        for policy in policies:
            policy.revision += 1
            policy.access_generation += 1
            record_mcp_protection_lifecycle_transition(
                policy=policy,
                from_lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
                to_lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
                reason_code=MCPProtectionSafeReason.NONE,
                metadata={"trigger": "workspace_restored"},
            )


def _block_relations(relations, endpoint_ids, reason) -> None:
    """Suspend the active relations and block their policies for ``reason``.

    ``endpoint_ids`` may be a lazy queryset; ``_bump_policies`` evaluates it
    after the relation update, exactly where the callers used to.
    """

    relations.filter(state=MCPProtectedFieldState.ACTIVE).update(
        state=MCPProtectedFieldState.SUSPENDED,
        safe_reason_code=reason,
    )
    _bump_policies(
        endpoint_ids,
        reason=reason,
        lifecycle_status=MCPProtectionLifecycleStatus.PROTECTION_BLOCKED,
    )


def _reactivate_policies_without_suspended_fields(endpoint_ids) -> None:
    """Return each policy with no suspended relation to ``ACTIVE``."""

    for policy in MCPProtectionPolicy.objects.filter(endpoint_id__in=endpoint_ids):
        if policy.protected_fields.filter(
            state=MCPProtectedFieldState.SUSPENDED
        ).exists():
            continue
        previous_status = policy.lifecycle_status
        policy.lifecycle_status = MCPProtectionLifecycleStatus.ACTIVE
        policy.safe_reason_code = MCPProtectionSafeReason.NONE
        policy.save(
            update_fields=["lifecycle_status", "safe_reason_code", "updated_on"]
        )
        record_mcp_protection_lifecycle_transition(
            policy=policy,
            from_lifecycle_status=previous_status,
            to_lifecycle_status=policy.lifecycle_status,
            reason_code=MCPProtectionSafeReason.NONE,
            metadata={"trigger": "hierarchy_restored"},
        )


def _set_hierarchy_protection_state(
    *, table_ids=None, database_ids=None, trashed: bool
):
    relation_filter = {}
    if table_ids is not None:
        relation_filter["field__table_id__in"] = table_ids
    if database_ids is not None:
        relation_filter["field__table__database_id__in"] = database_ids
    relations = MCPProtectedField.objects.filter(**relation_filter)
    if not relations.exists():
        return
    endpoint_ids = list(
        relations.values_list("policy__endpoint_id", flat=True).distinct()
    )
    if trashed:
        _block_relations(
            relations, endpoint_ids, MCPProtectionSafeReason.POLICY_RELATION_INVALID
        )
        return

    # A parent can be restored before all of its children. Keep the policy
    # blocked until every stable field identity is usable again.
    relations.filter(
        state=MCPProtectedFieldState.SUSPENDED,
        safe_reason_code=MCPProtectionSafeReason.POLICY_RELATION_INVALID,
        field__trashed=False,
        field__table__trashed=False,
        field__table__database__trashed=False,
    ).update(
        state=MCPProtectedFieldState.ACTIVE,
        safe_reason_code=MCPProtectionSafeReason.NONE,
    )
    _bump_policies(endpoint_ids)
    _reactivate_policies_without_suspended_fields(endpoint_ids)


def _snapshot_field_state(pk) -> dict | None:
    """Return the stored content-blind field state, or ``None`` if absent.

    An adapter that cannot be resolved is itself an unprovable conversion. Keep
    the ``None`` field-type sentinel so the post-save hook blocks the policy
    rather than allowing a potentially lossy value through.
    """

    previous = (
        Field.objects_and_trash.filter(pk=pk)
        .values("content_type_id", "trashed", "name")
        .first()
    )
    if previous is None:
        return None
    try:
        previous_model = ContentType.objects.get_for_id(
            previous["content_type_id"]
        ).model_class()
        previous["field_type"] = field_type_registry.get_by_model(previous_model).type
    except Exception:
        previous["field_type"] = None
    return previous


def _capture_field_state(sender, instance: Field, **kwargs):
    if not isinstance(instance, Field):
        return
    if not instance.pk:
        # ``change_polymorphic_type_to`` deletes the old child row with
        # ``keep_parents=True`` before saving the replacement. Django clears the
        # instance primary key during that delete, so retain the snapshot captured
        # by the pre-delete receiver below for the replacement save.
        if not hasattr(instance, "_mcp_protection_previous_state"):
            instance._mcp_protection_previous_state = None
        return
    instance._mcp_protection_previous_state = _snapshot_field_state(instance.pk)


def _capture_field_delete_state(sender, instance: Field, **kwargs):
    """Retain protected-field state across polymorphic child replacement.

    The upstream conversion helper deletes the old child object before creating
    the new one.  A pre-save-only guard cannot see that conversion because the
    delete clears the in-memory primary key.  Keep a content-blind snapshot on
    the object so the replacement save can still reject unsupported adapters.
    """

    if not isinstance(instance, Field) or not instance.pk:
        return
    previous = _snapshot_field_state(instance.pk)
    if previous is None:
        return
    instance._mcp_protection_previous_state = previous
    instance._mcp_protection_relation_exists = MCPProtectedField.objects.filter(
        field_id=instance.pk
    ).exists()


_UNSUPPORTED_PROTECTED_CONVERSION_TYPES = frozenset(
    {
        "autonumber",
        "count",
        "created_by",
        "created_on",
        "form_view_edit_row",
        "formula",
        "last_modified",
        "last_modified_by",
        "lookup",
        "password",
        "rollup",
        "uuid",
    }
)


def _supported_protected_field_conversion(
    previous_type: str | None, current_type: str | None
) -> bool:
    """Allow only conversions with a value-preserving, JSON-safe leaf type.

    Derived/read-only and password adapters can replace or reconstruct their
    stored representation during a schema change. Protection remains present,
    but the endpoint is blocked until the owner explicitly reviews and
    reactivates it. Ordinary editable field types keep their stable relation and
    simply invalidate old tokens through the policy generation bump.
    """

    return bool(previous_type and current_type) and not (
        previous_type in _UNSUPPORTED_PROTECTED_CONVERSION_TYPES
        or current_type in _UNSUPPORTED_PROTECTED_CONVERSION_TYPES
    )


def _safe_current_field_type(instance: Field) -> str | None:
    try:
        return instance.get_type().type
    except Exception:
        return None


def _field_changed(sender, instance: Field, created: bool, **kwargs):
    if not isinstance(instance, Field):
        return
    previous = getattr(instance, "_mcp_protection_previous_state", None)
    changed_type = (
        previous is not None and previous["content_type_id"] != instance.content_type_id
    )
    changed_trash = previous is not None and previous["trashed"] != instance.trashed
    changed_name = previous is not None and previous["name"] != instance.name
    if not created and not changed_type and not changed_trash and not changed_name:
        return
    relations = MCPProtectedField.objects.filter(field_id=instance.id)
    if not relations.exists():
        return
    with transaction.atomic():
        hierarchy_trashed = (
            instance.trashed
            or instance.table.trashed
            or instance.table.database.trashed
        )
        if hierarchy_trashed:
            _block_relations(
                relations,
                relations.values_list("policy__endpoint_id", flat=True),
                MCPProtectionSafeReason.POLICY_RELATION_INVALID,
            )
        elif changed_type and not _supported_protected_field_conversion(
            previous.get("field_type"),
            _safe_current_field_type(instance),
        ):
            _block_relations(
                relations,
                relations.values_list("policy__endpoint_id", flat=True),
                MCPProtectionSafeReason.FIELD_TYPE_CONVERSION_UNSUPPORTED,
            )
        elif changed_type or changed_trash or changed_name:
            # Only reached when ``hierarchy_trashed`` is false, so the field,
            # its table and its database are all untrashed here.
            if changed_trash:
                relations.filter(
                    state=MCPProtectedFieldState.SUSPENDED,
                    safe_reason_code=MCPProtectionSafeReason.POLICY_RELATION_INVALID,
                ).update(
                    state=MCPProtectedFieldState.ACTIVE,
                    safe_reason_code=MCPProtectionSafeReason.NONE,
                )
            endpoint_ids = list(
                relations.values_list("policy__endpoint_id", flat=True).distinct()
            )
            _bump_policies(endpoint_ids)
            if changed_trash:
                _reactivate_policies_without_suspended_fields(endpoint_ids)


def _reject_unsupported_protected_field_conversion(
    sender, instance: Field, **kwargs
) -> None:
    """Prevent an unsupported type change from landing before review.

    The post-save lifecycle hook still marks legacy/direct ORM changes blocked,
    but normal field updates must not first rewrite the column and then leave a
    protected policy unusable.  A protected relation can be removed explicitly
    before the conversion, or the conversion can proceed when both adapters are
    value-preserving.
    """

    if not isinstance(instance, Field):
        return
    previous = getattr(instance, "_mcp_protection_previous_state", None)
    if previous is None:
        return
    if previous["content_type_id"] == instance.content_type_id:
        return
    relation_exists = getattr(instance, "_mcp_protection_relation_exists", None)
    if relation_exists is None:
        relation_exists = bool(
            instance.pk
            and MCPProtectedField.objects.filter(field_id=instance.id).exists()
        )
    if not relation_exists:
        return
    if _supported_protected_field_conversion(
        previous.get("field_type"), _safe_current_field_type(instance)
    ):
        return
    raise ValidationError(
        "Unsupported field-type conversion is blocked while the field is protected."
    )


@transaction.atomic
def _workspace_changed(sender, instance: Workspace, created: bool, **kwargs):
    previous = getattr(instance, "_mcp_protection_previous_trash_state", None)
    if not created and previous is not None and previous != instance.trashed:
        _suspend_workspace_policies(instance.id, instance.trashed)


def _capture_hierarchy_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._mcp_protection_previous_trash_state = None
        return
    instance._mcp_protection_previous_trash_state = (
        sender.objects_and_trash.filter(pk=instance.pk)
        .values_list("trashed", flat=True)
        .first()
    )


@transaction.atomic
def _table_changed(sender, instance: Table, created: bool, **kwargs):
    previous = getattr(instance, "_mcp_protection_previous_trash_state", None)
    if not created and previous is not None and previous != instance.trashed:
        _set_hierarchy_protection_state(
            table_ids=[instance.id], trashed=instance.trashed
        )


@transaction.atomic
def _database_changed(sender, instance: Database, created: bool, **kwargs):
    previous = getattr(instance, "_mcp_protection_previous_trash_state", None)
    if not created and previous is not None and previous != instance.trashed:
        _set_hierarchy_protection_state(
            database_ids=[instance.id], trashed=instance.trashed
        )


@transaction.atomic
def _workspace_user_changed(sender, instance: WorkspaceUser, **kwargs):
    endpoint_ids = MCPEndpoint.objects.filter(
        user_id=instance.user_id, workspace_id=instance.workspace_id
    ).values_list("id", flat=True)
    if not WorkspaceUser.objects.filter(
        user_id=instance.user_id, workspace_id=instance.workspace_id
    ).exists():
        _bump_policies(
            endpoint_ids,
            reason=MCPProtectionSafeReason.MEMBERSHIP_CHANGED,
            lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        )
    else:
        _bump_policies(endpoint_ids)


@transaction.atomic
def _workspace_user_deleted(sender, instance: WorkspaceUser, **kwargs):
    _workspace_user_changed(sender, instance)


@transaction.atomic
def _user_changed(sender, instance, **kwargs):
    previous = getattr(instance, "_mcp_protection_previous_active_state", None)
    if previous is not None and previous == instance.is_active:
        return
    endpoint_ids = MCPEndpoint.objects.filter(user_id=instance.id).values_list(
        "id", flat=True
    )
    if not instance.is_active:
        _bump_policies(
            endpoint_ids,
            reason=MCPProtectionSafeReason.USER_INACTIVE,
            lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        )
        return
    # Account reactivation is deliberately not an authority grant.  Keep the
    # endpoint suspended until its owner explicitly reviews the policy and
    # calls the reactivation path, which rotates the endpoint key.
    _bump_policies(endpoint_ids)


@transaction.atomic
def _user_profile_changed(sender, instance: UserProfile, **kwargs):
    endpoint_ids = MCPEndpoint.objects.filter(user_id=instance.user_id).values_list(
        "id", flat=True
    )
    if instance.to_be_deleted:
        _bump_policies(
            endpoint_ids,
            reason=MCPProtectionSafeReason.USER_INACTIVE,
            lifecycle_status=MCPProtectionLifecycleStatus.SUSPENDED,
        )


def _capture_user_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._mcp_protection_previous_active_state = None
        return
    instance._mcp_protection_previous_active_state = (
        sender.objects.filter(pk=instance.pk)
        .values_list("is_active", flat=True)
        .first()
    )


def _capture_endpoint_state(sender, instance: MCPEndpoint, **kwargs):
    if not instance.pk:
        instance._mcp_protection_previous_key = None
        return
    instance._mcp_protection_previous_key = (
        MCPEndpoint.objects_and_trash.filter(pk=instance.pk)
        .values_list("key", flat=True)
        .first()
    )


@transaction.atomic
def _endpoint_changed(sender, instance: MCPEndpoint, created: bool, **kwargs):
    previous_key = getattr(instance, "_mcp_protection_previous_key", None)
    if not created and previous_key is not None and previous_key != instance.key:
        policy = MCPProtectionPolicy.objects.filter(endpoint_id=instance.id).first()
        if (
            policy is not None
            and policy.lifecycle_status != MCPProtectionLifecycleStatus.ACTIVE
        ):
            _bump_policies([instance.id])
            return
        _bump_policies(
            [instance.id],
            reason=MCPProtectionSafeReason.CREDENTIAL_ROTATED,
            lifecycle_status=MCPProtectionLifecycleStatus.PROTECTION_BLOCKED,
        )


def connect_mcp_protection_lifecycle() -> None:
    post_save.connect(
        create_empty_mcp_protection_policy,
        sender=MCPEndpoint,
        dispatch_uid="arabase_create_empty_mcp_protection_policy",
    )
    pre_save.connect(
        _capture_field_state,
        sender=None,
        dispatch_uid="arabase_capture_mcp_protection_field_state",
    )
    pre_delete.connect(
        _capture_field_delete_state,
        sender=None,
        dispatch_uid="arabase_capture_mcp_protection_field_delete_state",
    )
    pre_save.connect(
        _reject_unsupported_protected_field_conversion,
        sender=None,
        dispatch_uid="arabase_reject_unsupported_mcp_field_conversion",
    )
    post_save.connect(
        _field_changed,
        sender=None,
        dispatch_uid="arabase_mcp_protection_field_changed",
    )
    pre_save.connect(
        _capture_hierarchy_state,
        sender=Workspace,
        dispatch_uid="arabase_capture_mcp_protection_workspace_state",
    )
    post_save.connect(
        _workspace_changed,
        sender=Workspace,
        dispatch_uid="arabase_mcp_protection_workspace_changed",
    )
    pre_save.connect(
        _capture_hierarchy_state,
        sender=Table,
        dispatch_uid="arabase_capture_mcp_protection_table_state",
    )
    post_save.connect(
        _table_changed,
        sender=Table,
        dispatch_uid="arabase_mcp_protection_table_changed",
    )
    pre_save.connect(
        _capture_hierarchy_state,
        sender=Database,
        dispatch_uid="arabase_capture_mcp_protection_database_state",
    )
    post_save.connect(
        _database_changed,
        sender=Database,
        dispatch_uid="arabase_mcp_protection_database_changed",
    )
    post_save.connect(
        _workspace_user_changed,
        sender=WorkspaceUser,
        dispatch_uid="arabase_mcp_protection_workspace_user_changed",
    )
    post_delete.connect(
        _workspace_user_deleted,
        sender=WorkspaceUser,
        dispatch_uid="arabase_mcp_protection_workspace_user_deleted",
    )
    post_save.connect(
        _user_changed,
        sender=get_user_model(),
        dispatch_uid="arabase_mcp_protection_user_changed",
    )
    pre_save.connect(
        _capture_user_state,
        sender=get_user_model(),
        dispatch_uid="arabase_capture_mcp_protection_user_state",
    )
    post_save.connect(
        _user_profile_changed,
        sender=UserProfile,
        dispatch_uid="arabase_mcp_protection_user_profile_changed",
    )
    pre_save.connect(
        _capture_endpoint_state,
        sender=MCPEndpoint,
        dispatch_uid="arabase_capture_mcp_protection_endpoint_state",
    )
    post_save.connect(
        _endpoint_changed,
        sender=MCPEndpoint,
        dispatch_uid="arabase_mcp_protection_endpoint_changed",
    )
