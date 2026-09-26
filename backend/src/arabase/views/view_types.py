from typing import Any, Dict, List, Optional, Set
from zipfile import ZipFile

from django.core.files.storage import Storage
from django.urls import include, path

from rest_framework import serializers

from arabase.api.html_page.errors import ERROR_HTML_PAGE_TOO_LARGE
from arabase.api.html_page.serializers import HtmlPageViewFieldOptionsSerializer
from arabase.views.constants import MAX_HTML_LENGTH, MAX_ROW_LIMIT
from arabase.views.csp import build_page_csp
from arabase.views.exceptions import HtmlPageTooLarge
from arabase.views.models import HtmlPageView, HtmlPageViewFieldOptions
from jadawel.contrib.database.table.models import Table
from jadawel.contrib.database.views.models import View
from jadawel.contrib.database.views.registries import ViewType
from jadawel.core.registries import ImportExportConfig
from jadawel.core.storage import ExportZipFile


class ContentSecurityPolicyField(serializers.Field):
    """Exposes the policy the client must inject when it renders the page.

    ``source="*"`` because the value is derived from the view rather than read
    off one of its columns. The registry always hands serializers the specific
    instance (``Instance.get_serializer`` calls ``.specific``), so
    ``allow_external_resources`` is guaranteed to be there.
    """

    def __init__(self, **kwargs):
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return build_page_csp(value.allow_external_resources)


class HtmlPageViewType(ViewType):
    """A view rendered from an author-supplied HTML document.

    The document is untrusted — it is written by an AI over MCP and by whoever
    can edit the view — so it is never rendered on the app's own origin. The
    client puts it in a sandboxed iframe and applies ``content_security_policy``
    from this serializer; see ``arabase.views.csp`` for why the policy looks the
    way it does.
    """

    type = "html_page"
    model_class = HtmlPageView
    field_options_model_class = HtmlPageViewFieldOptions
    field_options_serializer_class = HtmlPageViewFieldOptionsSerializer
    allowed_fields = ["html", "allow_external_resources", "row_limit"]
    field_options_allowed_fields = ["hidden", "order"]
    serializer_field_names = [
        "html",
        "allow_external_resources",
        "row_limit",
        "content_security_policy",
    ]
    serializer_field_overrides = {
        "content_security_policy": ContentSecurityPolicyField(
            help_text=(
                "The Content-Security-Policy the client must apply to the iframe "
                "that renders this page. Computed by the server; a client that "
                "ignores it is rendering untrusted HTML unprotected."
            ),
        ),
    }

    api_exceptions_map = {
        HtmlPageTooLarge: ERROR_HTML_PAGE_TOO_LARGE,
    }

    can_filter = True
    can_sort = True
    can_share = True
    can_list_rows = True
    has_public_info = True

    can_group_by = False
    can_decorate = False
    can_aggregate_field = False
    can_set_default_values = False

    # v1 fetches rows when the page loads and on an explicit refresh. Turning
    # this on would make every row edit broadcast to every open public page for
    # a view type that mostly renders summaries; it can be revisited once
    # someone actually wants a live-ticking page.
    when_shared_publicly_requires_realtime_events = False

    def before_public_info(self, view: HtmlPageView, user) -> None:
        """Enforce the artifact binding before the generic public serializer runs."""

        from arabase.mcp.protection.artifact_boundary import (
            artifact_rest_boundary,
            page_runtime_access,
        )

        with artifact_rest_boundary():
            page_runtime_access(view, audience="public", user=user)

    def handle_view_update(self, values: dict, view: HtmlPageView, user):
        """Return a safe pending result for direct REST source edits."""

        from arabase.mcp.protection.artifact_boundary import artifact_rest_boundary
        from arabase.mcp.protection.artifact_commands import (
            human_page_update_as_artifact,
        )

        # Core PATCH runs this hook inside a transaction, so the 423 rolls it back.
        with artifact_rest_boundary():
            return human_page_update_as_artifact(user=user, view=view, values=values)

    def get_api_urls(self):
        from arabase.api.html_page import urls as api_urls

        return [
            path("html-page/", include(api_urls, namespace=self.type)),
        ]

    def prepare_values(self, values, table, user):
        """Clamp the two values a caller could use to hurt the browser."""

        html = values.get("html")
        if html is not None and len(html) > MAX_HTML_LENGTH:
            raise HtmlPageTooLarge(
                f"The page HTML is {len(html)} bytes, which is over the "
                f"{MAX_HTML_LENGTH} byte limit."
            )

        row_limit = values.get("row_limit")
        if row_limit is not None:
            values["row_limit"] = max(1, min(int(row_limit), MAX_ROW_LIMIT))

        return super().prepare_values(values, table, user)

    def export_serialized(
        self,
        html_page: View,
        import_export_config: ImportExportConfig,
        cache: Dict,
        files_zip: Optional[ExportZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """Carry the document and field options into the export.

        Without this, duplicating a view or a database silently produces an
        empty page — the failure is quiet and only shows up much later.
        """

        serialized = super().export_serialized(
            html_page, import_export_config, cache, files_zip, storage
        )

        serialized["html"] = html_page.html
        serialized["allow_external_resources"] = html_page.allow_external_resources
        serialized["row_limit"] = html_page.row_limit
        serialized["field_options"] = [
            {
                "id": field_option.id,
                "field_id": field_option.field_id,
                "hidden": field_option.hidden,
                "order": field_option.order,
            }
            for field_option in html_page.get_field_options()
        ]

        return serialized

    def import_serialized(
        self,
        table: Table,
        serialized_values: Dict[str, Any],
        import_export_config: ImportExportConfig,
        id_mapping: Dict[str, Any],
        cache: Dict,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Optional[View]:
        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop("field_options", [])

        html_page_view = super().import_serialized(
            table,
            serialized_copy,
            import_export_config,
            id_mapping,
            cache,
            files_zip,
            storage,
        )

        if html_page_view is not None:
            mapping = id_mapping.setdefault("arabase_html_page_view_field_options", {})

            for field_option in field_options:
                field_option_copy = field_option.copy()
                field_option_id = field_option_copy.pop("id")
                field_option_copy["field_id"] = id_mapping["database_fields"][
                    field_option["field_id"]
                ]
                field_option_object = HtmlPageViewFieldOptions.objects.create(
                    html_page_view=html_page_view, **field_option_copy
                )
                mapping[field_option_id] = field_option_object.id

        return html_page_view

    def export_prepared_values(self, view: HtmlPageView) -> Dict[str, Any]:
        values = super().export_prepared_values(view)
        values["html"] = view.html
        values["allow_external_resources"] = view.allow_external_resources
        values["row_limit"] = view.row_limit
        return values

    def view_created(self, view):
        """Start a new page with every field in the feed.

        A page is code written against the row shape, so making the author
        reveal each field before they can read it is friction for no gain — the
        gallery reveals three because a card only has room for three.

        Only at creation, though. Core's ``prepare_field_options`` hides a field
        added *later* when the view is public or when the author has already
        hidden something, and that caution is worth keeping: a shared page is
        served to anonymous visitors, and a column added next month should not
        become public on its own.
        """

        field_options = view.get_field_options(create_if_missing=True)
        HtmlPageViewFieldOptions.objects.filter(
            id__in=[option.id for option in field_options]
        ).update(hidden=False)

    def get_visible_field_options_in_order(self, html_page_view: HtmlPageView):
        return (
            html_page_view.get_field_options(create_if_missing=True)
            .filter(hidden=False)
            .order_by("order", "field__id")
        )

    def get_hidden_fields(
        self,
        view: HtmlPageView,
        field_ids_to_check: Optional[List[int]] = None,
    ) -> Set[int]:
        """Only an explicit ``hidden=True`` option hides a field here.

        The gallery treats a missing field option as hidden because its card
        shows three fields. A page is code written against the row shape, so a
        field nobody has configured yet should arrive rather than vanish.
        """

        field_options_by_field_id = {
            field_option.field_id: field_option
            for field_option in view.htmlpageviewfieldoptions_set.all()
        }

        fields = view.table.field_set.all()
        if field_ids_to_check is not None:
            fields = [f for f in fields if f.id in field_ids_to_check]

        return {
            field.id
            for field in fields
            if field.id in field_options_by_field_id
            and field_options_by_field_id[field.id].hidden
        }

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("htmlpageviewfieldoptions_set")
