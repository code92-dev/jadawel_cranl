"""Runtime boundary for MCP-authored HTML page artifacts.

The page itself is an untrusted template.  This module decides whether a page
document or row feed may expose a protected data projection: it validates the
durable approval binding and reports the artifact status.  The commands that
create drafts and approvals live in a separate, higher-level module.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable

from rest_framework.exceptions import APIException

from arabase.mcp.protection.artifact_fingerprints import (
    audience_fingerprint,
    configuration_fingerprint,
    manifest_fingerprint,
    provenance_for,
    sha256_text,
)
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactAudience,
    ArtifactDraft,
    ArtifactDraftStatus,
    ArtifactManifestField,
    HtmlPageArtifactState,
)
from arabase.mcp.protection.policy_state import (
    get_mcp_protection_policy_state,
    protected_output_fields,
)
from arabase.views.models import HtmlPageView
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.views.models import (
    ViewFilter,
    ViewGroupBy,
    ViewSort,
)
from jadawel.contrib.database.views.operations import UpdateViewOperationType
from jadawel.core.handler import CoreHandler
from jadawel.core.mcp.errors import SafeMCPToolError
from jadawel.core.mcp.models import MCPEndpoint


class ArtifactExposureBlocked(APIException):
    """Fixed in-product error used when a protected artifact is not renderable."""

    status_code = 423
    default_code = "MCP_ARTIFACT_UNAVAILABLE"
    default_detail = {
        "code": "MCP_ARTIFACT_UNAVAILABLE",
        "message": "This page is temporarily unavailable until its protected artifact is approved.",
    }


@contextmanager
def artifact_rest_boundary():
    """Fail an HTTP artifact path closed when protection cannot be proven.

    SafeMCPToolError is the MCP protocol's fixed error; over REST it becomes the
    fixed, content-blind 423 so no exception text or reason code leaks.
    """

    try:
        yield
    except SafeMCPToolError as exc:
        raise ArtifactExposureBlocked() from exc


@dataclass(frozen=True, slots=True)
class ArtifactRuntimeAccess:
    """The safe projection a page feed may hand to its sandbox."""

    required: bool
    allowed_protected_field_ids: frozenset[int] = frozenset()
    public_only: bool = False


# Request-scoped memo.
#
# One artifact request can resolve the same endpoint's policy and protected
# output several times.  Inside ``request_scope()`` the policy and the output
# of each (endpoint, table) pair are computed once.  Only successful results are
# stored, and an endpoint of ``None`` always bypasses the memo, so its
# fail-closed path runs exactly as without a scope.  Masking (egress and the
# interceptor) never uses this memo: it always loads a fresh policy after the
# read.
_request_cache: ContextVar[dict | None] = ContextVar(
    "mcp_artifact_request_cache", default=None
)


@contextmanager
def request_scope():
    """Share one memo for the duration of the block, or of the decorated call.

    Re-entrant: a nested scope reuses the outer memo, which is dropped only
    when the outermost scope exits.
    """

    if _request_cache.get() is not None:
        yield
        return
    token = _request_cache.set({})
    try:
        yield
    finally:
        _request_cache.reset(token)


def _cached(key, compute: Callable[[], Any]) -> Any:
    """Return ``compute()``, memoized under ``key`` inside a request scope."""

    cache = _request_cache.get()
    if cache is None or key is None:
        return compute()
    if key in cache:
        return cache[key]
    value = compute()
    cache[key] = value
    return value


def _endpoint_key(endpoint: MCPEndpoint | None) -> int | None:
    return endpoint.pk if endpoint is not None else None


def _policy_for_endpoint(endpoint: MCPEndpoint):
    endpoint_pk = _endpoint_key(endpoint)
    key = ("policy", endpoint_pk) if endpoint_pk is not None else None

    def load():
        try:
            return get_mcp_protection_policy_state(endpoint)
        except Exception as exc:
            # Policy-state failures already map to a fixed MCP error.  The
            # artifact boundary uses its own fixed in-product state and must not
            # expose why.
            raise ArtifactExposureBlocked() from exc

    return _cached(key, load)


def protected_output_for_view(
    view: HtmlPageView, endpoint: MCPEndpoint
) -> tuple[Any, ...]:
    endpoint_pk = _endpoint_key(endpoint)
    key = ("output", endpoint_pk, view.table_id) if endpoint_pk is not None else None

    def compute():
        policy = _policy_for_endpoint(endpoint)
        if not policy.has_protected_fields:
            return ()
        return protected_output_fields(
            view.table_id,
            policy.protected_fields,
            endpoint.workspace_id,
        )

    return _cached(key, compute)


def view_query_uses_protected_fields(view: HtmlPageView, endpoint: MCPEndpoint) -> bool:
    """Return whether a page's membership/order depends on protected output."""

    if endpoint is None:
        return False
    output_ids = {item.field_id for item in protected_output_for_view(view, endpoint)}
    if not output_ids:
        return False
    return (
        ViewFilter.objects.filter(view_id=view.id, field_id__in=output_ids).exists()
        or ViewSort.objects.filter(view_id=view.id, field_id__in=output_ids).exists()
        or ViewGroupBy.objects.filter(view_id=view.id, field_id__in=output_ids).exists()
    )


def _manifest_for_draft(draft: ArtifactDraft) -> list[ArtifactManifestField]:
    return list(
        draft.manifest_fields.select_related("field").order_by("stable_field_id")
    )


def _validate_manifest_against_view(
    draft: ArtifactDraft,
    output_fields: tuple[Any, ...],
    manifest: list[ArtifactManifestField],
) -> list[ArtifactManifestField]:
    expected_ids = list(draft.requested_field_ids)
    actual_ids = [item.stable_field_id for item in manifest]
    if actual_ids != sorted(expected_ids) or len(actual_ids) != len(set(actual_ids)):
        raise ArtifactExposureBlocked()
    output_by_id = {item.field_id: item for item in output_fields}
    pairs = []
    for item in manifest:
        output = output_by_id.get(item.stable_field_id)
        if output is None or item.field is None:
            raise ArtifactExposureBlocked()
        if (
            item.field_id != item.stable_field_id
            or item.table_id_snapshot != item.field.table_id
            or item.field_name_snapshot != item.field.name
            or item.provenance != provenance_for(output)
        ):
            raise ArtifactExposureBlocked()
        pairs.append((item.stable_field_id, item.provenance))
    if manifest_fingerprint(pairs) != draft.manifest_fingerprint:
        raise ArtifactExposureBlocked()
    return manifest


def _active_approval_for_audience(
    view_id: int, audience: str
) -> ArtifactApproval | None:
    """Return the newest live approval for one audience.

    The state row keeps a pointer to the most recently approved projection for
    compact status responses, but private and public approvals are independent
    authorities.  Looking them up by audience prevents a public approval from
    silently replacing (or expanding) a private one.
    """

    return (
        ArtifactApproval.objects.select_related("draft", "endpoint")
        .filter(view_id=view_id, audience=audience, revoked_at__isnull=True)
        .order_by("-approved_at", "-id")
        .first()
    )


# Endpoint resolution.
#
# ArtifactDraft.endpoint and ArtifactApproval.endpoint are non-null CASCADE
# foreign keys, so an existing draft or approval always names an endpoint. Only
# HtmlPageArtifactState.endpoint is nullable (SET_NULL once the endpoint is
# deleted). Each caller picks its own precedence among these sources; the orders
# differ on purpose and are pinned by test_artifact_endpoint_precedence.py.


def _latest_draft(view_id: int) -> ArtifactDraft | None:
    """Return the newest draft, by ``ArtifactDraft.Meta.ordering``."""

    return ArtifactDraft.objects.filter(view_id=view_id).first()


def _newest_live_approval(view_id: int) -> ArtifactApproval | None:
    """Return the newest unrevoked approval of any audience, with its draft."""

    return (
        ArtifactApproval.objects.select_related("draft")
        .filter(view_id=view_id, revoked_at__isnull=True)
        .order_by("-approved_at", "-id")
        .first()
    )


def _endpoint_of(record) -> MCPEndpoint | None:
    return record.endpoint if record is not None else None


def _first_endpoint(*candidates: Callable[[], Any]) -> Any:
    """Return the first non-``None`` candidate, calling each only when reached."""

    for candidate in candidates:
        value = candidate()
        if value is not None:
            return value
    return None


def _page_artifact_summary(
    view: HtmlPageView, state: HtmlPageArtifactState
) -> dict[str, Any]:
    approval = _newest_live_approval(view.id)
    pending_draft = ArtifactDraft.objects.filter(
        view=view, status=ArtifactDraftStatus.PENDING
    ).first()
    latest_draft = _latest_draft(view.id)
    selected_draft = (
        approval.draft
        if approval is not None
        else pending_draft
        if pending_draft is not None
        else latest_draft
    )
    if approval is not None:
        artifact_state = "approved"
    elif state.public_only:
        artifact_state = "public_only"
    elif pending_draft is not None:
        artifact_state = "pending_approval"
    else:
        artifact_state = "blocked"
    return {
        "view_id": view.id,
        "artifact_state": artifact_state,
        "target_generation": state.target_generation,
        "approval_id": approval.id if approval is not None else None,
        "draft_id": (
            approval.draft_id
            if approval is not None
            else pending_draft.id
            if pending_draft is not None
            else None
        ),
        "audience": (
            approval.audience
            if approval is not None
            else pending_draft.audience
            if pending_draft is not None
            else None
        ),
        # Summary: the newest live approval of any audience, then the latest
        # draft, then the state's endpoint.
        "endpoint_id": _first_endpoint(
            lambda: approval.endpoint_id if approval else None,
            lambda: latest_draft.endpoint_id if latest_draft else None,
            lambda: state.endpoint_id,
        ),
        "protected_field_ids": list(
            (
                approval.draft.requested_field_ids
                if approval is not None
                else pending_draft.requested_field_ids
                if pending_draft is not None
                else latest_draft.requested_field_ids
                if latest_draft is not None
                else []
            )
        ),
        # This projection is deliberately content-blind: reviewers can verify
        # the exact stable field identities and render-affecting shape without
        # receiving candidate HTML, filter values, row values, or credentials.
        "manifest": [
            {
                "field_id": item.stable_field_id,
                "provenance": item.provenance,
            }
            for item in (
                selected_draft.manifest_fields.order_by("stable_field_id")
                if selected_draft is not None
                else ()
            )
        ],
        "view_configuration": {
            "table_id": view.table_id,
            "row_limit": view.row_limit,
            "public": view.public,
            "allow_external_resources": view.allow_external_resources,
            "filter_type": view.filter_type,
            "filter_count": ViewFilter.objects.filter(view_id=view.id).count(),
            "sort_count": ViewSort.objects.filter(view_id=view.id).count(),
            "group_count": ViewGroupBy.objects.filter(view_id=view.id).count(),
        },
    }


def _validated_active_approval(
    *,
    view: HtmlPageView,
    state: HtmlPageArtifactState,
    audience: str,
    approval: ArtifactApproval | None,
    user=None,
) -> ArtifactRuntimeAccess:
    """Validate ``approval``, the result of ``_active_approval_for_audience``."""

    if approval is None and state.public_only:
        if (
            state.active_approval is not None
            and state.active_approval.revoked_at is None
        ):
            raise ArtifactExposureBlocked()
        return ArtifactRuntimeAccess(required=True, public_only=True)
    if state.public_only:
        return ArtifactRuntimeAccess(required=True, public_only=True)
    if approval is None:
        raise ArtifactExposureBlocked()
    if audience == ArtifactAudience.PUBLIC and not view.public:
        raise ArtifactExposureBlocked()
    if audience == ArtifactAudience.AUTHENTICATED and user is not None:
        allowed = CoreHandler().check_permissions(
            user,
            UpdateViewOperationType.type,
            workspace=view.table.database.workspace,
            context=view,
            raise_permission_exceptions=False,
        )
        if allowed is not True:
            raise ArtifactExposureBlocked()
    # ``target_generation`` is a view-level status counter.  It can advance
    # when an independent audience (private/public) is approved, so it is not
    # itself an authority check for this audience.  Content/configuration,
    # policy generations, and the audience fingerprint below are the exact
    # bindings; explicit replacement/revocation marks the old approval dead.
    if approval.content_digest != sha256_text(view.html):
        raise ArtifactExposureBlocked()
    if approval.configuration_fingerprint != configuration_fingerprint(view):
        raise ArtifactExposureBlocked()
    if approval.audience_fingerprint != audience_fingerprint(view, audience):
        raise ArtifactExposureBlocked()
    policy = _policy_for_endpoint(approval.endpoint)
    if (
        policy.revision != approval.policy_revision
        or policy.access_generation != approval.access_generation
        or approval.endpoint.workspace_id != view.table.database.workspace_id
    ):
        raise ArtifactExposureBlocked()
    output_fields = protected_output_for_view(view, approval.endpoint)
    manifest = _validate_manifest_against_view(
        approval.draft, output_fields, _manifest_for_draft(approval.draft)
    )
    return ArtifactRuntimeAccess(
        required=True,
        allowed_protected_field_ids=frozenset(
            item.stable_field_id for item in manifest
        ),
    )


def _runtime_access(
    view: HtmlPageView, audience: str, user
) -> tuple[
    ArtifactRuntimeAccess,
    HtmlPageArtifactState | None,
    ArtifactApproval | None,
]:
    """Return the runtime access with the state and live approval it checked.

    The state is ``None`` only for an unmanaged view, whose access is never
    required.
    """

    state = (
        HtmlPageArtifactState.objects.select_related(
            "endpoint", "active_approval__draft__endpoint"
        )
        .filter(view=view)
        .first()
    )
    if state is None:
        # View duplication/import copies the HTML but intentionally does not
        # copy artifact state or approvals.  Treat an exact copy of a managed
        # protected page as blocked until it goes through the draft/approval
        # boundary; otherwise the unmanaged copy would fall through to the
        # legacy feed and could expose the same protected rows.
        source_digest = sha256_text(view.html)
        candidate_states = (
            HtmlPageArtifactState.objects.select_related("endpoint", "view")
            .filter(view__table_id=view.table_id)
            .exclude(view_id=view.id)
        )
        for candidate_state in candidate_states:
            if candidate_state.view is None:
                continue
            if sha256_text(candidate_state.view.html) != source_digest:
                continue
            if protected_output_for_view(view, candidate_state.endpoint):
                raise ArtifactExposureBlocked()
        return ArtifactRuntimeAccess(required=False), None, None
    # Runtime access: the live audience approval, then the state's endpoint,
    # then the latest draft.
    approval = _active_approval_for_audience(view.id, audience)
    endpoint = _first_endpoint(
        lambda: _endpoint_of(approval),
        lambda: state.endpoint,
        lambda: _endpoint_of(_latest_draft(view.id)),
    )
    if endpoint is None:
        raise ArtifactExposureBlocked()
    output_fields = protected_output_for_view(view, endpoint)
    if not output_fields:
        return ArtifactRuntimeAccess(required=False), state, approval
    if view_query_uses_protected_fields(view, endpoint):
        raise ArtifactExposureBlocked()
    access = _validated_active_approval(
        view=view, state=state, audience=audience, approval=approval, user=user
    )
    return access, state, approval


@request_scope()
def page_runtime_access(
    view: HtmlPageView,
    *,
    audience: str = ArtifactAudience.AUTHENTICATED,
    user=None,
) -> ArtifactRuntimeAccess:
    """Validate the durable binding before a page document or row feed is read."""

    return _runtime_access(view, audience, user)[0]


@request_scope()
def page_feed_field_ids(
    view: HtmlPageView,
    *,
    audience: str = ArtifactAudience.AUTHENTICATED,
    user=None,
) -> set[int] | None:
    """Return the allowed field projection, or ``None`` for the legacy path."""

    # A required access always carries the state and the live audience
    # approval it was validated against, so both are reused here.
    access, state, approval = _runtime_access(view, audience, user)
    if not access.required:
        return None
    # Feed projection: the live audience approval, then the latest draft, then
    # the state's endpoint.
    endpoint = _first_endpoint(
        lambda: _endpoint_of(approval),
        lambda: _endpoint_of(_latest_draft(view.id)),
        lambda: state.endpoint,
    )
    if endpoint is None:
        raise ArtifactExposureBlocked()
    output_ids = {item.field_id for item in protected_output_for_view(view, endpoint)}
    # The view type supplies the authoritative active field options.
    visible_ids = set(
        HtmlPageViewType()
        .get_visible_field_options_in_order(view)
        .values_list("field_id", flat=True)
    )
    return (visible_ids - output_ids) | set(access.allowed_protected_field_ids)


def _feed_query_endpoint(view: HtmlPageView) -> MCPEndpoint | None:
    """Resolve the endpoint whose policy the page feed's query is checked against."""

    # Feed query: the newest live approval of any audience, then the state's
    # endpoint, then the latest draft.
    return _first_endpoint(
        lambda: _endpoint_of(_newest_live_approval(view.id)),
        lambda: _endpoint_of(
            HtmlPageArtifactState.objects.filter(view_id=view.id).first()
        ),
        lambda: _endpoint_of(_latest_draft(view.id)),
    )


@request_scope()
def page_feed_projection(
    view: HtmlPageView, *, audience: str, user, search
) -> set[int] | None:
    """Gate a page row feed and return its allowed field projection.

    ``None`` means the legacy, unmanaged feed.  A managed feed refuses any
    truthy search, and any view whose filters, sorts or groups depend on
    protected output.
    """

    allowed_field_ids = page_feed_field_ids(view, audience=audience, user=user)
    if allowed_field_ids is not None and (
        # The feed's search can inspect every visible field.  Once a protected
        # projection is approved, accepting an arbitrary search term would make
        # a protected value a membership oracle even if the response cells were
        # later masked.
        search or view_query_uses_protected_fields(view, _feed_query_endpoint(view))
    ):
        raise ArtifactExposureBlocked()
    return allowed_field_ids


@request_scope()
def artifact_status_for_view(view: HtmlPageView) -> dict[str, Any]:
    state = HtmlPageArtifactState.objects.filter(view=view).first()
    if state is None:
        return {"artifact_state": "unmanaged"}
    summary = _page_artifact_summary(view, state)
    approval = state.active_approval
    if approval is not None and approval.revoked_at is None:
        try:
            _validated_active_approval(
                view=view,
                state=state,
                audience=approval.audience,
                approval=_active_approval_for_audience(view.id, approval.audience),
            )
        except ArtifactExposureBlocked:
            summary.update(
                {
                    "artifact_state": "blocked",
                    "approval_id": None,
                }
            )
    return summary
