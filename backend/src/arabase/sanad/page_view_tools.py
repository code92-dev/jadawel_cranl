"""Sanad's tools for Page views (صفحة): HTML documents fed with a view's rows.

A Page view is written by an AI; until now only through an MCP client. These
tools let Sanad do it from inside Jadawel, as the signed-in administrator:
writes take the same route as the view's own REST PATCH, so a page under MCP
artifact protection still goes through its approval boundary, and every
overwrite first keeps the previous document as a revision. They are offered
only once the ``html-pages`` skill is loaded, and they check a document for the
mistakes that make a page render blank (misspelt field names, network calls,
external files) so any model gets told before the user sees it.
"""

import re
from typing import Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools import SanadEndpoint, SanadTool

SKILL = "html-pages"

SAMPLE_ROW_COUNT = 5
"""Enough rows to show the data's real shape (nulls, options, links)."""

MAX_RETURNED_HTML = 60_000
"""A longer document is cut in the result so one read cannot flood the chat."""


class CreatePageViewInput(BaseModel):
    table_id: int = Field(..., description="The table whose rows the page shows.")
    name: str = Field(..., description="The page's name, in the user's language.")
    row_limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Rows handed to the page (default 200)."
    )


class GetPageViewInput(BaseModel):
    view_id: int = Field(
        ..., description="The page's number (a Page view's ID), as the user gives it."
    )
    include_html: bool = Field(
        True, description="false to skip the current document (only the data)."
    )


class WritePageViewInput(BaseModel):
    view_id: int = Field(..., description="The Page view to write.")
    html: str = Field(
        ...,
        description="The complete document, <!doctype html> … </html>, with its "
        "CSS and JavaScript inline. It replaces the whole current document.",
    )
    name: Optional[str] = Field(None, description="A new name for the page.")
    row_limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Rows handed to the page."
    )


class PageEdit(BaseModel):
    find: str = Field(
        ..., description="Exact text in the current document; must occur once."
    )
    replace: str = Field(..., description="The text to put in its place.")


class EditPageViewInput(BaseModel):
    view_id: int = Field(..., description="The Page view to edit.")
    edits: list[PageEdit] = Field(
        ...,
        min_length=1,
        description="Replacements applied in order, each on the result of the "
        "previous one.",
    )


class ListPageViewRevisionsInput(BaseModel):
    view_id: int = Field(..., description="The Page view.")


class RestorePageViewRevisionInput(BaseModel):
    view_id: int = Field(..., description="The Page view.")
    revision_id: int = Field(..., description="From list_page_view_revisions.")


def _get_page_view(endpoint: SanadEndpoint, view_id: int):
    from arabase.mcp.page.services import _get_page_view as get_page_view

    return get_page_view(endpoint.user, endpoint.workspace, view_id)


def _fields(view) -> list[dict]:
    """The fields the page receives, in the order it receives them."""

    from arabase.views.view_types import HtmlPageViewType

    fields = []
    options = HtmlPageViewType().get_visible_field_options_in_order(view)
    for option in options.select_related("field"):
        field = option.field.specific
        item = {
            "id": field.id,
            "name": field.name,
            "type": field.get_type().type,
        }
        if hasattr(field, "select_options"):
            item["options"] = [
                {"value": choice.value, "color": choice.color}
                for choice in field.select_options.all()
            ]
        fields.append(item)
    return fields


def _rows(endpoint: SanadEndpoint, view, fields: list[dict]) -> tuple[int, list]:
    """The row count and a sample, shaped like ``row.values`` in the page."""

    from jadawel.contrib.database.api.rows.serializers import (
        serialize_rows_for_response,
    )
    from jadawel.contrib.database.views.handler import ViewHandler

    model = view.table.get_model()
    queryset = ViewHandler().get_queryset(endpoint.user, view, model=model)
    names = {field["name"] for field in fields}
    sample = [
        {key: value for key, value in row.items() if key == "id" or key in names}
        for row in serialize_rows_for_response(
            list(queryset[:SAMPLE_ROW_COUNT]), model, user_field_names=True
        )
    ]
    return queryset.count(), sample


def _summary(view) -> dict:
    return {
        "view_id": view.id,
        "name": view.name,
        "table_id": view.table_id,
        "table_name": view.table.name,
        "database_id": view.table.database_id,
        "row_limit": view.row_limit,
        "allow_external_resources": view.allow_external_resources,
        "is_public": view.public,
        "public_path": f"/public/page/{view.slug}" if view.public else None,
        "html_characters": len(view.html),
    }


def _describe(endpoint: SanadEndpoint, view, include_html: bool) -> dict:
    fields = _fields(view)
    row_count, sample = _rows(endpoint, view, fields)
    result = {
        **_summary(view),
        "fields": fields,
        "row_count": row_count,
        "truncated": row_count > view.row_limit,
        "row_sample": sample,
    }
    if include_html:
        html = view.html
        result["html"] = html[:MAX_RETURNED_HTML]
        if len(html) > MAX_RETURNED_HTML:
            result["html_cut"] = (
                f"Only the first {MAX_RETURNED_HTML} of {len(html)} characters "
                "are shown; change it with edit_page_view."
            )
    return result


# ---------------------------------------------------------------------------
# Checks a model gets back after writing
# ---------------------------------------------------------------------------

_VALUE_NAME = re.compile(r"""values\s*\[\s*(['"`])((?:(?!\1).)+)\1\s*\]""")
_NETWORK = re.compile(r"\bfetch\s*\(|XMLHttpRequest|new\s+WebSocket|EventSource")
_STORAGE = re.compile(r"localStorage|sessionStorage|document\.cookie|indexedDB")
_EXTERNAL = re.compile(
    r"""<(?:script|link|img|iframe)\b[^>]*\b(?:src|href)\s*=\s*["']?(?:https?:)?//"""
    r"""|@import\s+(?:url\()?["']?(?:https?:)?//|url\(\s*["']?(?:https?:)?//""",
    re.IGNORECASE,
)
_NAVIGATION = re.compile(
    r"window\.open\s*\(|(?:top|window|document)\.location(?:\.href)?\s*=|<form\b"
)
_PHYSICAL = re.compile(
    r"(?:margin|padding|border)-(?:left|right)\s*:|text-align\s*:\s*(?:left|right)"
    r"|[;{\s](?:left|right)\s*:\s*-?\d",
    re.IGNORECASE,
)
_ARABIC_DIGITS = re.compile(
    r"""(?:toLocaleString|toLocaleDateString|NumberFormat|DateTimeFormat)\s*\(\s*"""
    r"""(['"])ar(?:-[A-Za-z]{2})?\1"""
)


def check_page_html(html: str, field_names: set[str], allow_external: bool) -> list:
    """Problems that make a page render wrong or blank, in words a model acts on."""

    warnings = []
    lowered = html.lower()
    if "<html" not in lowered or "<body" not in lowered:
        warnings.append(
            "Not a complete document: write <!doctype html><html>…<body>…</body>"
            "</html>."
        )
    unknown = sorted(
        {match.group(2) for match in _VALUE_NAME.finditer(html)} - field_names
    )
    if unknown:
        warnings.append(
            f"row.values has no {', '.join(map(repr, unknown))}: those read as "
            f"undefined. The page's fields are {', '.join(sorted(field_names))}."
        )
    if field_names and "onData" not in html:
        warnings.append(
            "The page never calls window.jadawel.onData, so it shows no rows. "
            "Render inside window.jadawel.onData(({ fields, rows, view }) => …)."
        )
    if _NETWORK.search(html):
        warnings.append(
            "fetch, XMLHttpRequest, WebSocket and EventSource are blocked in a "
            "page: use the rows onData hands over."
        )
    if _STORAGE.search(html):
        warnings.append(
            "localStorage, sessionStorage, cookies and indexedDB throw in a "
            "page: keep state in JavaScript variables."
        )
    if not allow_external and _EXTERNAL.search(html):
        warnings.append(
            "External files (CDN scripts, stylesheets, web fonts, remote images) "
            "do not load: external resources are off for this page. Inline the "
            "CSS and JS, draw with inline SVG, use system fonts."
        )
    if _NAVIGATION.search(html):
        warnings.append(
            "Links that leave the page, window.open and forms are blocked in a "
            "page; filters and tabs have to work inside it."
        )
    physical = len(_PHYSICAL.findall(html))
    if physical:
        warnings.append(
            f"{physical} left/right rule(s): they break in Arabic (RTL). Use "
            "margin-inline-start/end, padding-inline, inset-inline-start/end and "
            "text-align: start/end."
        )
    if _ARABIC_DIGITS.search(html):
        warnings.append(
            "An 'ar' locale formats numbers with Arabic-Indic digits; the house "
            "style is Western digits: use 'en-US' (or 'ar-SA-u-nu-latn')."
        )
    return warnings


def _write(endpoint: SanadEndpoint, view, values: dict) -> dict:
    """Save through the same route as the view's REST PATCH.

    ``handle_view_update`` sends a page under MCP artifact protection to its
    approval boundary and hands back the pending result; otherwise the update
    is an ordinary undoable action. The previous document is kept first, as a
    revision, because an AI overwrite is a normal-looking call.
    """

    from arabase.mcp.protection.artifact_boundary import artifact_rest_boundary
    from arabase.views.handler import HtmlPageRevisionHandler
    from arabase.views.view_types import HtmlPageViewType
    from jadawel.contrib.database.views.actions import UpdateViewActionType

    view_type = HtmlPageViewType()
    with artifact_rest_boundary():
        pending = view_type.handle_view_update(values, view, endpoint.user)
    if pending is not None:
        view.refresh_from_db()
        return {
            **_summary(view),
            "status": "awaiting_approval",
            "note": "This page is under MCP data protection: the new document "
            "is a draft until an administrator approves it in the page's "
            "settings.",
        }

    if "html" in values and values["html"] != view.html:
        HtmlPageRevisionHandler().snapshot(view, endpoint.user)
    view = UpdateViewActionType.do(endpoint.user, view, **values)
    field_names = {field["name"] for field in _fields(view)}
    return {
        **_summary(view),
        "status": "saved",
        "warnings": check_page_html(
            view.html, field_names, view.allow_external_resources
        ),
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def create_page_view(endpoint: SanadEndpoint, args: CreatePageViewInput) -> dict:
    from arabase.views.view_types import HtmlPageViewType
    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.actions import CreateViewActionType

    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    kwargs = {"name": args.name, "html": ""}
    if args.row_limit is not None:
        kwargs["row_limit"] = args.row_limit
    with transaction.atomic():
        view = CreateViewActionType.do(
            endpoint.user, table, HtmlPageViewType.type, **kwargs
        )
    return _describe(endpoint, view.specific, include_html=False)


def get_page_view(endpoint: SanadEndpoint, args: GetPageViewInput) -> dict:
    view = _get_page_view(endpoint, args.view_id)
    return _describe(endpoint, view, include_html=args.include_html)


def write_page_view(endpoint: SanadEndpoint, args: WritePageViewInput) -> dict:
    view = _get_page_view(endpoint, args.view_id)
    values = {"html": args.html}
    if args.name is not None:
        values["name"] = args.name
    if args.row_limit is not None:
        values["row_limit"] = args.row_limit
    with transaction.atomic():
        return _write(endpoint, view, values)


def edit_page_view(endpoint: SanadEndpoint, args: EditPageViewInput) -> dict:
    view = _get_page_view(endpoint, args.view_id)
    html = view.html
    for number, edit in enumerate(args.edits, start=1):
        found = html.count(edit.find)
        if found != 1:
            raise ValueError(
                f"Edit {number}: the text to find occurs {found} times; it must "
                "occur exactly once. Quote more of the surrounding text, or read "
                "the page again with get_page_view."
            )
        html = html.replace(edit.find, edit.replace)
    with transaction.atomic():
        return _write(endpoint, view, {"html": html})


def list_page_view_revisions(
    endpoint: SanadEndpoint, args: ListPageViewRevisionsInput
) -> list[dict]:
    from arabase.mcp.page.services import list_page_revisions

    revisions = list_page_revisions(endpoint.user, endpoint.workspace, args.view_id)
    return [
        {
            "revision_id": revision["revision_id"],
            "created_on": revision["created_on"],
            "characters": revision["html_bytes"],
        }
        for revision in revisions
    ]


def restore_page_view_revision(
    endpoint: SanadEndpoint, args: RestorePageViewRevisionInput
) -> dict:
    from arabase.views.handler import HtmlPageRevisionHandler

    view = _get_page_view(endpoint, args.view_id)
    revision = HtmlPageRevisionHandler().get_revision(view, args.revision_id)
    with transaction.atomic():
        return _write(endpoint, view, {"html": revision.html})


def get_page_view_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "create_page_view",
            "Create a Page view (صفحة) on a table: an HTML page fed with the "
            "table's live rows. Not an application page. Returns its number, "
            "fields and sample rows.",
            CreatePageViewInput,
            create_page_view,
            skill=SKILL,
        ),
        SanadTool(
            "get_page_view",
            "Read a Page view by its number: its fields, row count, sample rows "
            "shaped as the page receives them, and the current HTML.",
            GetPageViewInput,
            get_page_view,
            skill=SKILL,
        ),
        SanadTool(
            "write_page_view",
            "Write a Page view's whole HTML document (it replaces the current "
            "one, which is kept as a revision). The result lists problems found.",
            WritePageViewInput,
            write_page_view,
            skill=SKILL,
        ),
        SanadTool(
            "edit_page_view",
            "Change part of a Page view's document with exact find/replace "
            "edits, without rewriting all of it.",
            EditPageViewInput,
            edit_page_view,
            skill=SKILL,
        ),
        SanadTool(
            "list_page_view_revisions",
            "List a Page view's earlier documents, newest first.",
            ListPageViewRevisionsInput,
            list_page_view_revisions,
            skill=SKILL,
        ),
        SanadTool(
            "restore_page_view_revision",
            "Put an earlier document back; the current one is kept as a revision.",
            RestorePageViewRevisionInput,
            restore_page_view_revision,
            skill=SKILL,
        ),
    ]
