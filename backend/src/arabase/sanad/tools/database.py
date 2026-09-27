"""Sanad's database tools: databases, tables, fields, rows and views.

Most are the MCP tools the fork already exposes to external AI clients: their
``_sync_call`` runs as a user in a workspace through
``jadawel.contrib.database.mcp.services``, which filters every query by that
user's permissions. Sanad calls them with the signed-in user, so the assistant
can never reach anything the person chatting could not reach themselves.

They are called directly rather than through ``mcp_tool_registry.call_sync``:
the registry's interceptor enforces a per-*MCP-endpoint* field-protection
policy, and a Sanad chat has no endpoint (the policy fails closed without one).

Views, filters and sorts have no MCP tool, so they are defined here on top of
the same action types the grid UI uses, which keeps undo and permission checks
identical to a manual edit.
"""

from typing import Optional

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import (
    SanadEndpoint,
    SanadTool,
    describe_doc,
    select_option_ids,
)

# MCP tools reused as-is. The page-authoring tools are left out on purpose:
# they bind drafts and approvals to a saved MCP endpoint.
REUSED_MCP_TOOLS = (
    "list_databases",
    "create_database",
    "list_tables",
    "get_table_schema",
    "create_table",
    "update_table",
    "delete_table",
    "create_fields",
    "update_fields",
    "delete_fields",
    "list_table_rows",
    "create_rows",
    "update_rows",
    "delete_rows",
)


class ListViewsInput(BaseModel):
    table_id: int = Field(..., description="The table whose views to list.")


class CreateViewInput(BaseModel):
    table_id: int = Field(..., description="The table to add the view to.")
    name: str = Field(..., description="The view name.")
    type: str = Field(
        "grid",
        description="One of: grid, gallery, kanban. For a form, use create_form.",
    )
    single_select_field_id: Optional[int] = Field(
        None,
        description=(
            "Kanban only: the single select field whose options become the "
            "kanban columns."
        ),
    )


class DeleteViewInput(BaseModel):
    view_id: int = Field(..., description="The view to delete.")


class AddViewFilterInput(BaseModel):
    view_id: int = Field(..., description="The view to filter.")
    field_id: int = Field(..., description="The field the condition applies to.")
    type: str = Field(
        ...,
        description=(
            "Filter type, e.g. equal, not_equal, contains, contains_not, "
            "higher_than, lower_than, empty, not_empty, boolean, "
            "single_select_equal, date_is, link_row_has."
        ),
    )
    value: str = Field(
        "",
        description="The value to compare with, as a string. Empty for "
        "empty/not_empty. Select filters take the option's text (or its ID); "
        "is_any_of takes several, comma-separated.",
    )


class AddViewSortInput(BaseModel):
    view_id: int = Field(..., description="The view to sort.")
    field_id: int = Field(..., description="The field to sort by.")
    order: str = Field("ASC", description="ASC or DESC.")


SUPPORTED_VIEW_TYPES = ("grid", "gallery", "kanban")


def _check_not_page_view(view) -> None:
    """A Page view shows no Filter or Sort button, so neither may Sanad add one.

    The backend still applies the ones saved earlier, but a rule nobody can see
    would silently change what the page receives.
    """

    if view.get_type().type == "html_page":
        raise ValueError(
            "A Page view has no filters or sorts. Filter and order the rows in "
            "the page's own code (the html-pages skill)."
        )


def _get_view(endpoint: SanadEndpoint, view_id: int):
    """Load a view in the chat's workspace that the user can see."""

    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.handler import ViewHandler

    view = ViewHandler().get_view(view_id)
    # Re-resolve the table through the permission-filtered service so a view in
    # another workspace, or in a table the user cannot list, looks missing.
    services.get_table(endpoint.user, endpoint.workspace, view.table_id)
    return view


def list_views(endpoint: SanadEndpoint, args: ListViewsInput) -> list[dict]:
    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.models import View
    from jadawel.contrib.database.views.operations import ListViewsOperationType
    from jadawel.core.handler import CoreHandler

    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    views = CoreHandler().filter_queryset(
        endpoint.user,
        ListViewsOperationType.type,
        View.objects.filter(table=table).order_by("order", "id"),
        workspace=endpoint.workspace,
    )
    return [
        {
            "id": view.id,
            "name": view.name,
            "type": view.get_type().type,
            "table_id": view.table_id,
        }
        for view in views.select_related("content_type")
    ]


def create_view(endpoint: SanadEndpoint, args: CreateViewInput) -> dict:
    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.actions import CreateViewActionType

    if args.type == "form":
        # Every field of a new form view starts disabled, so it would ask
        # nothing; create_form picks the questions in the same call.
        raise ValueError(
            "Build a form with create_form (load the forms skill): a form view "
            "created here asks no questions."
        )
    if args.type not in SUPPORTED_VIEW_TYPES:
        raise ValueError(
            f"Unsupported view type {args.type!r}; use one of "
            f"{', '.join(SUPPORTED_VIEW_TYPES)}."
        )
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    kwargs = {"name": args.name}
    if args.type == "kanban":
        if args.single_select_field_id is None:
            raise ValueError("A kanban view needs single_select_field_id.")
        # The kanban view type validates the field's type and table itself.
        kwargs["single_select_field"] = args.single_select_field_id
    view = CreateViewActionType.do(endpoint.user, table, args.type, **kwargs)
    return {
        "id": view.id,
        "name": view.name,
        "type": args.type,
        "table_id": table.id,
        "database_id": table.database_id,
    }


def delete_view(endpoint: SanadEndpoint, args: DeleteViewInput) -> dict:
    from jadawel.contrib.database.views.actions import DeleteViewActionType

    view = _get_view(endpoint, args.view_id)
    DeleteViewActionType.do(endpoint.user, view)
    return {"deleted_view_id": args.view_id}


def add_view_filter(endpoint: SanadEndpoint, args: AddViewFilterInput) -> dict:
    from jadawel.contrib.database.fields.handler import FieldHandler
    from jadawel.contrib.database.views.actions import CreateViewFilterActionType

    view = _get_view(endpoint, args.view_id)
    _check_not_page_view(view)
    field = FieldHandler().get_field(args.field_id)
    if field.table_id != view.table_id:
        raise ValueError("That field belongs to a different table.")
    view_filter = CreateViewFilterActionType.do(
        endpoint.user,
        view,
        field,
        args.type,
        select_option_ids(field, args.type, args.value),
    )
    return {"id": view_filter.id, "view_id": view.id, "table_id": view.table_id}


def add_view_sort(endpoint: SanadEndpoint, args: AddViewSortInput) -> dict:
    from jadawel.contrib.database.fields.handler import FieldHandler
    from jadawel.contrib.database.views.actions import CreateViewSortActionType

    order = args.order.upper()
    if order not in ("ASC", "DESC"):
        raise ValueError("order must be ASC or DESC.")
    view = _get_view(endpoint, args.view_id)
    _check_not_page_view(view)
    field = FieldHandler().get_field(args.field_id)
    if field.table_id != view.table_id:
        raise ValueError("That field belongs to a different table.")
    view_sort = CreateViewSortActionType.do(endpoint.user, view, field, order)
    return {"id": view_sort.id, "view_id": view.id, "table_id": view.table_id}


def get_tools() -> list[SanadTool]:
    from jadawel.core.mcp.registries import mcp_tool_registry

    tools = []
    for name in REUSED_MCP_TOOLS:
        mcp_tool = mcp_tool_registry.get(name)
        tools.append(
            SanadTool(
                name=name,
                description=describe_doc(mcp_tool.__class__.__doc__),
                input_schema=mcp_tool.input_schema,
                run=mcp_tool._sync_call,
            )
        )
    return tools + [
        SanadTool(
            "list_views",
            "List the views (grid, gallery, form, kanban…) of a table.",
            ListViewsInput,
            list_views,
        ),
        SanadTool(
            "create_view",
            "Create a view on a table. Use it to give the user a filtered or "
            "sorted perspective, a gallery, or a kanban board.",
            CreateViewInput,
            create_view,
        ),
        SanadTool(
            "delete_view",
            "Delete a view. Needs the user's approval.",
            DeleteViewInput,
            delete_view,
        ),
        SanadTool(
            "add_view_filter",
            "Add one filter condition to a view. Call get_table_schema first "
            "for the field ID.",
            AddViewFilterInput,
            add_view_filter,
        ),
        SanadTool(
            "add_view_sort",
            "Sort a view by a field, ascending (ASC) or descending (DESC).",
            AddViewSortInput,
            add_view_sort,
        ),
    ]
