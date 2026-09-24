import uuid

from django.conf import settings
from django.db import models

from jadawel.contrib.database.fields.models import Field
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.mixins import CreatedAndUpdatedOnMixin


class MCPProtectionLifecycleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    PROTECTION_BLOCKED = "protection_blocked", "Protection blocked"


class MCPProtectedFieldState(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"


class MCPProtectionSafeReason(models.TextChoices):
    NONE = "", "None"
    POLICY_COUNT_MISMATCH = "POLICY_COUNT_MISMATCH", "Policy count mismatch"
    POLICY_STATE_INVALID = "POLICY_STATE_INVALID", "Policy state invalid"
    POLICY_RELATION_INVALID = "POLICY_RELATION_INVALID", "Policy relation invalid"
    WORKSPACE_SUSPENDED = "WORKSPACE_SUSPENDED", "Workspace suspended"
    MEMBERSHIP_CHANGED = "MEMBERSHIP_CHANGED", "Membership changed"
    USER_INACTIVE = "USER_INACTIVE", "User inactive"
    CREDENTIAL_ROTATED = "CREDENTIAL_ROTATED", "Credential rotated"
    FIELD_TYPE_CONVERSION_UNSUPPORTED = (
        "FIELD_TYPE_CONVERSION_UNSUPPORTED",
        "Field type conversion requires review",
    )
    PROTECTION_REDIS_UNAVAILABLE = (
        "PROTECTION_REDIS_UNAVAILABLE",
        "Protection Redis unavailable",
    )
    PROTECTION_VAULT_UNAVAILABLE = (
        "PROTECTION_VAULT_UNAVAILABLE",
        "Protection vault unavailable",
    )
    PROTECTION_KEY_UNAVAILABLE = (
        "PROTECTION_KEY_UNAVAILABLE",
        "Protection fingerprint key unavailable",
    )


class MCPProtectionPolicy(CreatedAndUpdatedOnMixin, models.Model):
    """The explicit, revisioned protection state for one MCP endpoint."""

    endpoint = models.OneToOneField(
        MCPEndpoint,
        on_delete=models.CASCADE,
        related_name="arabase_protection_policy",
    )
    revision = models.PositiveBigIntegerField(default=1)
    access_generation = models.PositiveBigIntegerField(default=1)
    lifecycle_status = models.CharField(
        max_length=32,
        choices=MCPProtectionLifecycleStatus.choices,
        default=MCPProtectionLifecycleStatus.ACTIVE,
    )
    safe_reason_code = models.CharField(
        max_length=64,
        choices=MCPProtectionSafeReason.choices,
        blank=True,
        default=MCPProtectionSafeReason.NONE,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(revision__gte=1),
                name="arabase_mcp_policy_revision_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(access_generation__gte=1),
                name="arabase_mcp_access_generation_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
                        safe_reason_code=MCPProtectionSafeReason.NONE,
                    )
                    | (
                        ~models.Q(lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE)
                        & ~models.Q(safe_reason_code=MCPProtectionSafeReason.NONE)
                    )
                ),
                name="arabase_mcp_policy_status_reason_consistent",
            ),
        ]


class MCPProtectedField(CreatedAndUpdatedOnMixin, models.Model):
    """A protected stable field identity belonging to an endpoint policy."""

    policy = models.ForeignKey(
        MCPProtectionPolicy,
        on_delete=models.CASCADE,
        related_name="protected_fields",
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.PROTECT,
        related_name="mcp_protection_relations",
    )
    state = models.CharField(
        max_length=16,
        choices=MCPProtectedFieldState.choices,
        default=MCPProtectedFieldState.ACTIVE,
    )
    safe_reason_code = models.CharField(
        max_length=64,
        choices=MCPProtectionSafeReason.choices,
        blank=True,
        default=MCPProtectionSafeReason.NONE,
    )

    class Meta:
        ordering = ("field_id",)
        constraints = [
            models.UniqueConstraint(
                fields=("policy", "field"),
                name="arabase_unique_mcp_policy_field",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        state=MCPProtectedFieldState.ACTIVE,
                        safe_reason_code=MCPProtectionSafeReason.NONE,
                    )
                    | (
                        models.Q(state=MCPProtectedFieldState.SUSPENDED)
                        & ~models.Q(safe_reason_code=MCPProtectionSafeReason.NONE)
                    )
                ),
                name="arabase_mcp_field_state_reason_consistent",
            ),
        ]
        indexes = [
            models.Index(
                fields=("field", "state"),
                name="ara_mcp_pf_field_state_idx",
            ),
            models.Index(
                fields=("policy", "state"),
                name="ara_mcp_pf_policy_state_idx",
            ),
        ]


class MCPProtectionCommand(CreatedAndUpdatedOnMixin, models.Model):
    """Bounded idempotency state for one composite endpoint creation command."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mcp_protection_commands",
    )
    idempotency_key = models.CharField(max_length=128)
    request_fingerprint = models.CharField(max_length=64)
    endpoint = models.OneToOneField(
        MCPEndpoint,
        on_delete=models.CASCADE,
        related_name="arabase_creation_command",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("actor", "idempotency_key"),
                name="arabase_unique_mcp_command_key",
            )
        ]
        indexes = [
            models.Index(
                fields=("actor", "created_on"),
                name="ara_mcp_cmd_actor_created_idx",
            )
        ]


class MCPProtectionEditCommand(CreatedAndUpdatedOnMixin, models.Model):
    """Bounded idempotency state for one endpoint policy replacement."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mcp_protection_edit_commands",
    )
    policy = models.ForeignKey(
        MCPProtectionPolicy,
        on_delete=models.CASCADE,
        related_name="edit_commands",
    )
    idempotency_key = models.CharField(max_length=128)
    request_fingerprint = models.CharField(max_length=64)
    resulting_revision = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("actor", "idempotency_key"),
                name="arabase_unique_mcp_edit_command_key",
            )
        ]
        indexes = [
            models.Index(
                fields=("actor", "created_on"),
                name="ara_mcp_edit_actor_created_idx",
            )
        ]


class MCPProtectionMutationAudit(CreatedAndUpdatedOnMixin, models.Model):
    """Content-blind audit record for a protected MCP row mutation."""

    endpoint = models.ForeignKey(
        MCPEndpoint,
        on_delete=models.SET_NULL,
        null=True,
        related_name="protection_mutation_audits",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mcp_protection_mutation_audits",
    )
    tool_type = models.CharField(max_length=64)
    table_id = models.PositiveBigIntegerField()
    row_count = models.PositiveIntegerField()
    outcome = models.CharField(max_length=24, default="success")
    policy_revision = models.PositiveBigIntegerField(default=0)
    access_generation = models.PositiveBigIntegerField(default=0)
    protected_field_ids = models.JSONField(default=list)

    class Meta:
        indexes = [
            models.Index(
                fields=("endpoint", "created_on"),
                name="ara_mcp_audit_ep_created_idx",
            )
        ]


class MCPMaskTokenRecord(models.Model):
    """One live mask token in the PostgreSQL vault.

    Holds exactly what the Redis vault holds: the SHA-256 digest of the raw
    handle, its binding, and a keyed fingerprint of the value. Never the handle,
    the value or a field name. The fingerprint key is not stored in the database,
    so a backup of this table cannot be brute-forced back to low-entropy values.
    """

    digest = models.CharField(max_length=64, primary_key=True)
    endpoint = models.ForeignKey(
        MCPEndpoint,
        on_delete=models.CASCADE,
        related_name="+",
    )
    expires_at = models.DateTimeField()
    record = models.JSONField()

    class Meta:
        indexes = [
            models.Index(fields=("expires_at",), name="ara_mcp_token_expiry_idx"),
            models.Index(
                fields=("endpoint", "expires_at"),
                name="ara_mcp_token_ep_expiry_idx",
            ),
        ]


class MCPProtectionLifecycleAudit(CreatedAndUpdatedOnMixin, models.Model):
    """Append-only, content-blind record of protection lifecycle transitions."""

    endpoint = models.ForeignKey(
        MCPEndpoint,
        on_delete=models.SET_NULL,
        null=True,
        related_name="protection_lifecycle_audits",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="mcp_protection_lifecycle_audits",
    )
    event_type = models.CharField(max_length=64)
    from_lifecycle_status = models.CharField(max_length=32, blank=True, default="")
    to_lifecycle_status = models.CharField(max_length=32, blank=True, default="")
    reason_code = models.CharField(max_length=64, blank=True, default="")
    policy_revision = models.PositiveBigIntegerField(null=True, blank=True)
    access_generation = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(
                fields=("endpoint", "created_on"),
                name="ara_mcp_lifecycle_created_idx",
            )
        ]


class ArtifactAudience(models.TextChoices):
    """The two deliberately separate runtime exposure scopes."""

    AUTHENTICATED = "authenticated", "Authenticated viewers"
    PUBLIC = "public", "Public viewers"


class ArtifactDraftStatus(models.TextChoices):
    PENDING = "pending", "Pending approval"
    APPROVED = "approved", "Approved"
    SUPERSEDED = "superseded", "Superseded"
    REVOKED = "revoked", "Revoked"


class ArtifactProvenance(models.TextChoices):
    DIRECT = "direct", "Direct protected field"
    DERIVED = "derived", "Derived protected field"


class HtmlPageArtifactState(CreatedAndUpdatedOnMixin, models.Model):
    """Durable runtime pointer for the protected artifact attached to a page."""

    view = models.OneToOneField(
        "arabase.HtmlPageView",
        on_delete=models.CASCADE,
        related_name="mcp_artifact_state",
    )
    endpoint = models.ForeignKey(
        MCPEndpoint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_states",
    )
    active_approval = models.ForeignKey(
        "arabase.ArtifactApproval",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_for_states",
    )
    target_generation = models.PositiveBigIntegerField(default=1)
    # A page that deliberately requested no protected fields can remain live
    # without a human approval, while the runtime still withholds the protected
    # projection.  ``False`` plus no approval means blocked, never public-only.
    public_only = models.BooleanField(default=False)


class ArtifactDraft(CreatedAndUpdatedOnMixin, models.Model):
    """An immutable candidate until an authorized human promotes it."""

    endpoint = models.ForeignKey(
        MCPEndpoint,
        on_delete=models.CASCADE,
        related_name="mcp_artifact_drafts",
    )
    view = models.ForeignKey(
        "arabase.HtmlPageView",
        on_delete=models.CASCADE,
        related_name="mcp_artifact_drafts",
    )
    candidate_html = models.TextField(blank=True)
    content_digest = models.CharField(max_length=64)
    configuration_fingerprint = models.CharField(max_length=64)
    manifest_fingerprint = models.CharField(max_length=64)
    requested_field_ids = models.JSONField(default=list)
    pending_view_values = models.JSONField(default=dict)
    audience = models.CharField(
        max_length=16,
        choices=ArtifactAudience.choices,
        default=ArtifactAudience.AUTHENTICATED,
    )
    status = models.CharField(
        max_length=16,
        choices=ArtifactDraftStatus.choices,
        default=ArtifactDraftStatus.PENDING,
    )
    nonce = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_drafts_submitted",
    )

    class Meta:
        ordering = ("-created_on", "-id")
        indexes = [
            models.Index(
                fields=("endpoint", "view", "status"),
                name="ara_art_draft_ep_view_idx",
            ),
            models.Index(
                fields=("view", "created_on"),
                name="ara_art_draft_view_created_idx",
            ),
        ]


class ArtifactManifestField(CreatedAndUpdatedOnMixin, models.Model):
    """A stable, content-blind field declaration made by the MCP caller."""

    draft = models.ForeignKey(
        ArtifactDraft,
        on_delete=models.CASCADE,
        related_name="manifest_fields",
    )
    field = models.ForeignKey(
        Field,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_manifest_fields",
    )
    stable_field_id = models.PositiveBigIntegerField()
    field_name_snapshot = models.CharField(max_length=255)
    table_id_snapshot = models.PositiveBigIntegerField()
    provenance = models.CharField(max_length=16, choices=ArtifactProvenance.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("draft", "stable_field_id"),
                name="ara_art_manifest_draft_field_unique",
            )
        ]
        indexes = [
            models.Index(
                fields=("stable_field_id", "provenance"),
                name="ara_art_manifest_field_idx",
            )
        ]


class ArtifactApproval(CreatedAndUpdatedOnMixin, models.Model):
    """Exact revision/audience binding that permits runtime projection."""

    draft = models.OneToOneField(
        ArtifactDraft,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    endpoint = models.ForeignKey(
        MCPEndpoint,
        on_delete=models.CASCADE,
        related_name="mcp_artifact_approvals",
    )
    view = models.ForeignKey(
        "arabase.HtmlPageView",
        on_delete=models.CASCADE,
        related_name="mcp_artifact_approvals",
    )
    content_digest = models.CharField(max_length=64)
    configuration_fingerprint = models.CharField(max_length=64)
    manifest_fingerprint = models.CharField(max_length=64)
    policy_revision = models.PositiveBigIntegerField()
    access_generation = models.PositiveBigIntegerField()
    target_generation = models.PositiveBigIntegerField()
    audience = models.CharField(max_length=16, choices=ArtifactAudience.choices)
    audience_fingerprint = models.CharField(max_length=64)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_approvals_granted",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(
                fields=("view", "audience", "revoked_at"),
                name="ara_art_ap_view_scope_idx",
            ),
            models.Index(
                fields=("endpoint", "policy_revision"),
                name="ara_art_ap_ep_rev_idx",
            ),
        ]


class ArtifactAuditEvent(CreatedAndUpdatedOnMixin, models.Model):
    """Append-only, content-blind audit trail for artifact transitions."""

    endpoint = models.ForeignKey(
        MCPEndpoint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_audit_events",
    )
    view = models.ForeignKey(
        "arabase.HtmlPageView",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_audit_events",
    )
    draft = models.ForeignKey(
        ArtifactDraft,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    approval = models.ForeignKey(
        ArtifactApproval,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mcp_artifact_audit_events",
    )
    event_type = models.CharField(max_length=32)
    audience = models.CharField(max_length=16, blank=True, default="")
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(
                fields=("view", "created_on"),
                name="ara_art_audit_view_created_idx",
            )
        ]
