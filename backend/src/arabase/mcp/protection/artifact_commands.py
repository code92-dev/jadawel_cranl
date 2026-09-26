"""Approval commands for MCP-authored HTML page artifacts.

This module owns the only transition that can attach a protected data
projection to a page template.  It intentionally stores hashes, stable
identities, and content-blind audit metadata; row values and mask handles never
enter an approval record.
"""

from __future__ import annotations

from typing import Any, Iterable

from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import PermissionDenied, ValidationError

from arabase.mcp.protection.artifact_boundary import (
    ArtifactExposureBlocked,
    _active_approval_for_audience,
    _endpoint_of,
    _first_endpoint,
    _latest_draft,
    _manifest_for_draft,
    _page_artifact_summary,
    _policy_for_endpoint,
    _validate_manifest_against_view,
    protected_output_for_view,
    request_scope,
    view_query_uses_protected_fields,
)
from arabase.mcp.protection.artifact_fingerprints import (
    audience_fingerprint,
    configuration_fingerprint,
    manifest_fingerprint,
    provenance_for,
    sha256_text,
    validate_artifact_html,
)
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactAudience,
    ArtifactAuditEvent,
    ArtifactDraft,
    ArtifactDraftStatus,
    ArtifactManifestField,
    HtmlPageArtifactState,
)
from arabase.views.constants import MAX_ROW_LIMIT
from arabase.views.handler import HtmlPageRevisionHandler
from arabase.views.models import HtmlPageView
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.operations import ReadFieldOperationType
from jadawel.contrib.database.views.operations import UpdateViewOperationType
from jadawel.core.exceptions import PermissionException
from jadawel.core.handler import CoreHandler
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.models import WorkspaceUser

# The only view settings a draft may carry alongside its HTML.
SAFE_PENDING_VIEW_KEYS = frozenset({"name", "allow_external_resources", "row_limit"})


def _audit(
    *,
    event_type: str,
    actor,
    endpoint: MCPEndpoint | None,
    view: HtmlPageView | None,
    draft: ArtifactDraft | None = None,
    approval: ArtifactApproval | None = None,
    audience: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    # Keep this helper deliberately restrictive: callers pass only ids/counts
    # and hashes, never the candidate HTML or row payload.
    ArtifactAuditEvent.objects.create(
        event_type=event_type,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        endpoint=endpoint,
        view=view,
        draft=draft,
        approval=approval,
        audience=audience,
        metadata=metadata or {},
    )


def _ensure_endpoint_owner_can_approve(
    user, draft: ArtifactDraft, manifest: list[ArtifactManifestField]
) -> None:
    endpoint = draft.endpoint
    view = draft.view
    if not getattr(user, "is_authenticated", False) or user.id != endpoint.user_id:
        raise PermissionDenied("Only the endpoint owner may approve this artifact.")
    if not user.is_active or (
        getattr(user, "profile", None) and user.profile.to_be_deleted
    ):
        raise PermissionDenied("The approver account is not active.")
    if not WorkspaceUser.objects.filter(
        user_id=user.id, workspace_id=endpoint.workspace_id
    ).exists():
        raise PermissionDenied("The approver is not an active workspace member.")
    try:
        CoreHandler().check_permissions(
            user,
            UpdateViewOperationType.type,
            workspace=view.table.database.workspace,
            context=view,
        )
        for item in manifest:
            if item.field is None:
                raise PermissionDenied("A manifest field is no longer available.")
            CoreHandler().check_permissions(
                user,
                ReadFieldOperationType.type,
                workspace=view.table.database.workspace,
                context=item.field,
            )
    except PermissionException as exc:
        raise PermissionDenied(
            "The approver cannot manage this protected page."
        ) from exc


def _get_or_create_state(view: HtmlPageView) -> HtmlPageArtifactState:
    state, _ = HtmlPageArtifactState.objects.get_or_create(view=view)
    return state


def _live_approvals(view: HtmlPageView) -> list[ArtifactApproval]:
    """Return every unrevoked approval of a view, in the database's order."""

    return list(
        ArtifactApproval.objects.select_related("draft").filter(
            view=view, revoked_at__isnull=True
        )
    )


def _revoke_approvals(
    approvals: Iterable[ArtifactApproval],
    *,
    reason: str,
    draft_status: str,
    now=None,
) -> None:
    """Revoke approvals and move their drafts to ``draft_status``.

    Without ``now`` every approval gets its own ``timezone.now()``.
    """

    for approval in approvals:
        approval.revoked_at = now if now is not None else timezone.now()
        approval.revocation_reason = reason
        approval.save(update_fields=["revoked_at", "revocation_reason", "updated_on"])
        approval.draft.status = draft_status
        approval.draft.save(update_fields=["status", "updated_on"])


def _safe_update_view(view: HtmlPageView, values: dict[str, Any], user) -> None:
    """Apply a content-blind artifact promotion without the undo HTML payload."""

    if view.html != values.get("html", view.html):
        HtmlPageRevisionHandler().snapshot(view, user)
    for key, value in values.items():
        setattr(view, key, value)
    fields = list(values.keys()) + ["updated_on"]
    view.save(update_fields=fields)


@transaction.atomic
@request_scope()
def submit_mcp_page_change(
    *,
    user,
    endpoint: MCPEndpoint,
    view: HtmlPageView,
    html: str,
    protected_field_ids: list[int],
    audience: str = ArtifactAudience.AUTHENTICATED,
    pending_view_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit a protected draft, or publish a public-only template safely."""

    validate_artifact_html(html)
    pending_view_values = pending_view_values or {}
    allowed_values = {
        key: value
        for key, value in pending_view_values.items()
        if key in SAFE_PENDING_VIEW_KEYS
    }
    if "row_limit" in allowed_values:
        allowed_values["row_limit"] = max(
            1, min(int(allowed_values["row_limit"]), MAX_ROW_LIMIT)
        )
    if audience not in ArtifactAudience.values:
        raise ValidationError({"audience": "Unsupported artifact audience."})
    if len(protected_field_ids) != len(set(protected_field_ids)):
        raise ValidationError({"protected_field_ids": "Field IDs must be unique."})

    output_fields = protected_output_for_view(view, endpoint)
    if view_query_uses_protected_fields(view, endpoint):
        raise ValidationError(
            {
                "view": (
                    "A page whose filters, sorts, or groups depend on protected "
                    "data cannot expose a protected artifact."
                )
            }
        )
    output_by_id = {item.field_id: item for item in output_fields}
    requested = sorted(protected_field_ids)
    if any(field_id not in output_by_id for field_id in requested):
        raise ValidationError(
            {
                "protected_field_ids": "Every requested field must be a protected output of this page."
            }
        )
    if audience == ArtifactAudience.PUBLIC and not view.public:
        raise ValidationError(
            {"audience": "A public approval requires a publicly shared page."}
        )

    # Both paths below change the live page: a publish replaces its HTML, and a
    # draft rebinds its governing endpoint, supersedes pending drafts and takes
    # it out of public-only mode. Either needs the permission to edit the view,
    # checked before any write. (Approving a draft requires it too.)
    CoreHandler().check_permissions(
        user,
        UpdateViewOperationType.type,
        workspace=view.table.database.workspace,
        context=view,
    )

    # A page that requests no protected projection is safe to publish directly;
    # the runtime marks it public-only and strips every protected output field.
    if not requested:
        state = _get_or_create_state(view)
        state.endpoint = endpoint
        _revoke_approvals(
            _live_approvals(view),
            reason="public_only_replacement",
            draft_status=ArtifactDraftStatus.REVOKED,
        )
        _safe_update_view(view, {"html": html, **allowed_values}, user)
        state.active_approval = None
        state.public_only = bool(output_fields)
        state.target_generation += 1
        state.save(
            update_fields=[
                "active_approval",
                "endpoint",
                "public_only",
                "target_generation",
                "updated_on",
            ]
        )
        _audit(
            event_type="public_only_published",
            actor=user,
            endpoint=endpoint,
            view=view,
            audience=audience,
            metadata={
                "content_digest": sha256_text(html),
                "protected_output_count": len(output_fields),
            },
        )
        return {
            **_page_artifact_summary(view, state),
            "status": "published",
            "protected_field_ids": [],
        }

    policy = _policy_for_endpoint(endpoint)
    manifest_pairs = [
        (field_id, provenance_for(output_by_id[field_id])) for field_id in requested
    ]

    state = _get_or_create_state(view)
    state.endpoint = endpoint
    ArtifactDraft.objects.filter(
        endpoint=endpoint,
        view=view,
        audience=audience,
        status=ArtifactDraftStatus.PENDING,
    ).update(status=ArtifactDraftStatus.SUPERSEDED)
    draft = ArtifactDraft.objects.create(
        endpoint=endpoint,
        view=view,
        candidate_html=html,
        content_digest=sha256_text(html),
        configuration_fingerprint=configuration_fingerprint(view, allowed_values),
        manifest_fingerprint=manifest_fingerprint(manifest_pairs),
        requested_field_ids=requested,
        pending_view_values=allowed_values,
        audience=audience,
        submitted_by=user if getattr(user, "is_authenticated", False) else None,
    )
    fields = {
        field.id: field
        for field in Field.objects.filter(id__in=requested).select_related("table")
    }
    manifest_rows = []
    for field_id, provenance in manifest_pairs:
        field = fields.get(field_id)
        if field is None:
            raise ArtifactExposureBlocked()
        manifest_rows.append(
            ArtifactManifestField(
                draft=draft,
                field=field,
                stable_field_id=field.id,
                field_name_snapshot=field.name,
                table_id_snapshot=field.table_id,
                provenance=provenance,
            )
        )
    ArtifactManifestField.objects.bulk_create(manifest_rows)
    state.public_only = False
    state.save(update_fields=["endpoint", "public_only", "updated_on"])
    _audit(
        event_type="draft_submitted",
        actor=user,
        endpoint=endpoint,
        view=view,
        draft=draft,
        audience=audience,
        metadata={
            "content_digest": draft.content_digest,
            "manifest_fingerprint": draft.manifest_fingerprint,
            "protected_field_count": len(requested),
            "policy_revision": policy.revision,
        },
    )
    return {
        **_page_artifact_summary(view, state),
        "status": "pending_approval",
        "draft_id": draft.id,
        "audience": audience,
        "protected_field_ids": requested,
    }


@transaction.atomic
@request_scope()
def approve_artifact_draft(*, user, draft_id: int) -> dict[str, Any]:
    draft = (
        ArtifactDraft.objects.select_related(
            "endpoint__workspace", "view__table__database__workspace"
        )
        .select_for_update(of=("self",))
        .get(id=draft_id)
    )
    manifest = _manifest_for_draft(draft)
    _ensure_endpoint_owner_can_approve(user, draft, manifest)
    if draft.status != ArtifactDraftStatus.PENDING:
        raise ValidationError({"draft_id": "Only a pending draft can be approved."})
    view = HtmlPageView.objects.select_for_update().get(id=draft.view_id)
    state = _get_or_create_state(view)
    output_fields = protected_output_for_view(view, draft.endpoint)
    _validate_manifest_against_view(draft, output_fields, manifest)
    if draft.content_digest != sha256_text(draft.candidate_html):
        raise ArtifactExposureBlocked()
    if draft.configuration_fingerprint != configuration_fingerprint(
        view, draft.pending_view_values
    ):
        raise ArtifactExposureBlocked()
    policy = _policy_for_endpoint(draft.endpoint)
    if draft.audience == ArtifactAudience.PUBLIC and not view.public:
        raise ArtifactExposureBlocked()
    if draft.audience not in ArtifactAudience.values:
        raise ArtifactExposureBlocked()

    old_approval = _active_approval_for_audience(view.id, draft.audience)
    _revoke_approvals(
        [old_approval] if old_approval is not None else [],
        reason="superseded",
        draft_status=ArtifactDraftStatus.SUPERSEDED,
    )

    _safe_update_view(
        view,
        {"html": draft.candidate_html, **draft.pending_view_values},
        user,
    )
    state.target_generation += 1
    state.public_only = False
    approval = ArtifactApproval.objects.create(
        draft=draft,
        endpoint=draft.endpoint,
        view=view,
        content_digest=draft.content_digest,
        configuration_fingerprint=draft.configuration_fingerprint,
        manifest_fingerprint=draft.manifest_fingerprint,
        policy_revision=policy.revision,
        access_generation=policy.access_generation,
        target_generation=state.target_generation,
        audience=draft.audience,
        audience_fingerprint=audience_fingerprint(view, draft.audience),
        approved_by=user,
        approved_at=timezone.now(),
    )
    draft.status = ArtifactDraftStatus.APPROVED
    draft.save(update_fields=["status", "updated_on"])
    state.active_approval = approval
    state.endpoint = draft.endpoint
    state.save(
        update_fields=[
            "active_approval",
            "endpoint",
            "public_only",
            "target_generation",
            "updated_on",
        ]
    )
    _audit(
        event_type="approved",
        actor=user,
        endpoint=draft.endpoint,
        view=view,
        draft=draft,
        approval=approval,
        audience=draft.audience,
        metadata={
            "content_digest": approval.content_digest,
            "manifest_fingerprint": approval.manifest_fingerprint,
            "policy_revision": approval.policy_revision,
            "access_generation": approval.access_generation,
            "target_generation": approval.target_generation,
        },
    )
    return {
        **_page_artifact_summary(view, state),
        "status": "approved",
        "approval_id": approval.id,
        "audience": approval.audience,
        "protected_field_ids": list(draft.requested_field_ids),
    }


@transaction.atomic
def revoke_artifact(
    *, user, view_id: int, reason: str = "manual_revocation"
) -> dict[str, Any]:
    view = (
        HtmlPageView.objects.select_for_update()
        .select_related("table__database")
        .get(id=view_id)
    )
    state = HtmlPageArtifactState.objects.select_for_update().get(view=view)
    # Revoke: the state's approval (even if revoked), then the latest draft.
    endpoint = _first_endpoint(
        lambda: _endpoint_of(state.active_approval),
        lambda: _endpoint_of(_latest_draft(view.id)),
    )
    if endpoint is None or endpoint.user_id != getattr(user, "id", None):
        raise PermissionDenied("Only the artifact endpoint owner may revoke it.")
    approvals = _live_approvals(view)
    approval = approvals[0] if approvals else None
    _revoke_approvals(
        approvals,
        reason=reason[:64],
        draft_status=ArtifactDraftStatus.REVOKED,
        now=timezone.now(),
    )
    if approvals:
        state.active_approval = None
    state.public_only = False
    state.target_generation += 1
    state.save(
        update_fields=[
            "active_approval",
            "public_only",
            "target_generation",
            "updated_on",
        ]
    )
    _audit(
        event_type="revoked",
        actor=user,
        endpoint=endpoint,
        view=view,
        audience=approval.audience if approval is not None else "",
        metadata={"reason": reason[:64], "target_generation": state.target_generation},
    )
    return {**_page_artifact_summary(view, state), "status": "revoked"}


@request_scope()
def human_page_update_as_artifact(
    *, user, view: HtmlPageView, values: dict[str, Any]
) -> dict[str, Any] | None:
    """Route a direct REST source edit through the same draft boundary as MCP."""

    if "html" not in values:
        return None
    state = HtmlPageArtifactState.objects.filter(view=view).first()
    if state is None:
        return None
    approval = state.active_approval
    live_approval = approval if approval and approval.revoked_at is None else None
    latest_draft = _latest_draft(view.id)
    # Human edit: the state's live approval, then the latest draft, then the
    # state's endpoint.
    endpoint = _first_endpoint(
        lambda: _endpoint_of(live_approval),
        lambda: _endpoint_of(latest_draft),
        lambda: state.endpoint,
    )
    if endpoint is None:
        return None
    output_fields = protected_output_for_view(view, endpoint)
    if not output_fields:
        return None
    draft = live_approval.draft if live_approval else latest_draft
    protected_field_ids = list(draft.requested_field_ids) if draft else []
    audience = (
        live_approval.audience
        if live_approval
        else draft.audience
        if draft
        else ArtifactAudience.AUTHENTICATED
    )
    return submit_mcp_page_change(
        user=user,
        endpoint=endpoint,
        view=view,
        html=values["html"],
        protected_field_ids=protected_field_ids,
        audience=audience,
        pending_view_values={
            key: value for key, value in values.items() if key != "html"
        },
    )
