"""Pure fingerprint helpers for MCP-authored HTML page artifacts.

Every helper here is side-effect free apart from reading view settings, and
none of them raises the artifact exposure error.  They produce the digests that
bind a draft or an approval to its HTML, view configuration, audience and
manifest, so their outputs are persisted and must stay byte-identical.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from rest_framework.exceptions import ValidationError

from arabase.mcp.protection.models import ArtifactAudience, ArtifactProvenance
from arabase.mcp.protection.tokens import MASK_TOKEN_RESERVED_KEY
from arabase.views.constants import MAX_HTML_LENGTH
from arabase.views.models import HtmlPageView
from jadawel.contrib.database.views.models import (
    ViewFilter,
    ViewFilterGroup,
    ViewGroupBy,
    ViewSort,
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def validate_artifact_html(html: str) -> None:
    if not isinstance(html, str):
        raise ValidationError({"html": "HTML must be a string."})
    if len(html.encode("utf-8")) > MAX_HTML_LENGTH:
        raise ValidationError({"html": "The page HTML is too large."})
    # The MCP envelope is deliberately reserved.  A substring check is safer
    # here than trying to parse arbitrary HTML or JavaScript and accidentally
    # accepting a token hidden in a script or attribute.
    if MASK_TOKEN_RESERVED_KEY in html:
        raise ValidationError(
            {"html": "Protected mask tokens cannot be stored in an artifact."}
        )


def view_configuration(view: HtmlPageView, overrides: dict[str, Any] | None = None):
    """Return a value-free fingerprint input for all render-affecting settings."""

    overrides = overrides or {}
    field_options = [
        {
            "field_id": option.field_id,
            "hidden": option.hidden,
            "order": option.order,
        }
        for option in view.get_field_options(create_if_missing=True)
    ]
    filters = [
        {
            "field_id": item.field_id,
            "type": item.type,
            # Filter values may themselves be sensitive.  They are included only
            # inside this one-way digest input, never persisted as metadata.
            "value_digest": canonical_digest(item.value),
            "group_id": item.group_id,
        }
        for item in ViewFilter.objects.filter(view_id=view.id).order_by("id")
    ]
    filter_groups = list(
        ViewFilterGroup.objects.filter(view_id=view.id)
        .order_by("id")
        .values("id", "filter_type", "parent_group_id")
    )
    sorts = list(
        ViewSort.objects.filter(view_id=view.id)
        .order_by("id")
        .values("field_id", "order")
    )
    groups = list(
        ViewGroupBy.objects.filter(view_id=view.id)
        .order_by("id")
        .values("field_id", "order")
    )
    values = {
        "view_id": view.id,
        "table_id": view.table_id,
        "field_options": field_options,
        "filter_type": overrides.get("filter_type", view.filter_type),
        "filters_disabled": overrides.get("filters_disabled", view.filters_disabled),
        "filters": filters,
        "filter_groups": filter_groups,
        "sorts": sorts,
        "groups": groups,
        "row_limit": overrides.get("row_limit", view.row_limit),
        "allow_external_resources": overrides.get(
            "allow_external_resources", view.allow_external_resources
        ),
        "public": overrides.get("public", view.public),
        "has_password": bool(
            overrides.get("public_view_password", view.public_view_password)
        ),
        "slug": view.slug,
    }
    return values


def configuration_fingerprint(
    view: HtmlPageView, overrides: dict[str, Any] | None = None
) -> str:
    return canonical_digest(view_configuration(view, overrides))


def audience_fingerprint(view: HtmlPageView, audience: str) -> str:
    if audience == ArtifactAudience.PUBLIC:
        # Do not retain the password hash.  Hashing the current boolean, slug,
        # and view identity makes share rotation/password changes invalidate the
        # approval while keeping the approval record content-blind.
        return canonical_digest(
            {
                "audience": audience,
                "view_id": view.id,
                "slug": view.slug,
                "public": view.public,
                "has_password": view.public_view_has_password,
            }
        )
    return canonical_digest(
        {
            "audience": audience,
            "view_id": view.id,
            "workspace_id": view.table.database.workspace_id,
        }
    )


def manifest_fingerprint(
    manifest: Iterable[tuple[int, str]],
) -> str:
    return canonical_digest(
        [
            {"field_id": field_id, "provenance": provenance}
            for field_id, provenance in sorted(manifest)
        ]
    )


def provenance_for(output) -> str:
    return (
        ArtifactProvenance.DIRECT
        if output.operation_class == "preserve_cell"
        else ArtifactProvenance.DERIVED
    )
