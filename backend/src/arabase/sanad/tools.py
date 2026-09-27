"""The actions Sanad can take inside a workspace.

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

from dataclasses import dataclass
from typing import Any, Callable, Optional

from django.contrib.auth.models import AbstractUser

from pydantic import BaseModel, Field, ValidationError

from jadawel.core.models import Workspace

# Tools that delete something, or put a workflow live so it acts on real data
# unattended. The model must get the user's explicit approval in the panel
# before any of them runs.
APPROVAL_TOOLS = frozenset(
    {
        "delete_table",
        "delete_fields",
        "delete_rows",
        "delete_view",
        "delete_page",
        "delete_automation_step",
        "publish_workflow",
        "delete_page_element",
        "delete_dashboard_widget",
    }
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


@dataclass
class SanadEndpoint:
    """The two attributes the database MCP tools read from an endpoint."""

    user: AbstractUser
    workspace: Workspace


@dataclass
class SanadTool:
    name: str
    description: str
    input_schema: type[BaseModel]
    run: Callable[[SanadEndpoint, Any], Any]
    skill: Optional[str] = None
    """Offered to the model only once this skill is loaded in the chat."""

    @property
    def needs_approval(self) -> bool:
        return self.name in APPROVAL_TOOLS

    def json_schema(self) -> dict:
        return self.input_schema.model_json_schema()

    def call(self, endpoint: SanadEndpoint, arguments: dict) -> Any:
        """Validate the model's arguments and run the tool.

        :raises ValidationError: when the arguments do not match the schema.
        """

        return self.run(endpoint, self.input_schema(**arguments))


# ---------------------------------------------------------------------------
# View tools
# ---------------------------------------------------------------------------


class ListViewsInput(BaseModel):
    table_id: int = Field(..., description="The table whose views to list.")


class CreateViewInput(BaseModel):
    table_id: int = Field(..., description="The table to add the view to.")
    name: str = Field(..., description="The view name.")
    type: str = Field(
        "grid",
        description="One of: grid, gallery, form, kanban.",
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


SUPPORTED_VIEW_TYPES = ("grid", "gallery", "form", "kanban")


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


SELECT_FILTER_TYPES = frozenset(
    {
        "single_select_equal",
        "single_select_not_equal",
        "single_select_is_any_of",
        "single_select_is_none_of",
        "multiple_select_has",
        "multiple_select_has_not",
    }
)


def _select_filter_value(field, args: "AddViewFilterInput") -> str:
    """A select filter's value as option IDs, the only form it matches.

    Models naturally write the option's text ("Open"); stored as-is, that
    filter matches nothing and the view silently shows every row, which once
    led a model to tell the user that filters are ignored.
    """

    if args.type not in SELECT_FILTER_TYPES or not args.value.strip():
        return args.value
    options = {
        option.value.strip().casefold(): str(option.id)
        for option in field.select_options.all()
    }
    valid_ids = set(options.values())
    ids = []
    for part in args.value.split(","):
        part = part.strip()
        if part in valid_ids:
            ids.append(part)
        elif part.casefold() in options:
            ids.append(options[part.casefold()])
        else:
            names = ", ".join(option.value for option in field.select_options.all())
            raise ValueError(f"{part!r} is not an option of this field: {names}.")
    return ",".join(ids)


def add_view_filter(endpoint: SanadEndpoint, args: AddViewFilterInput) -> dict:
    from jadawel.contrib.database.fields.handler import FieldHandler
    from jadawel.contrib.database.views.actions import CreateViewFilterActionType

    view = _get_view(endpoint, args.view_id)
    field = FieldHandler().get_field(args.field_id)
    if field.table_id != view.table_id:
        raise ValueError("That field belongs to a different table.")
    view_filter = CreateViewFilterActionType.do(
        endpoint.user, view, field, args.type, _select_filter_value(field, args)
    )
    return {"id": view_filter.id, "view_id": view.id, "table_id": view.table_id}


def add_view_sort(endpoint: SanadEndpoint, args: AddViewSortInput) -> dict:
    from jadawel.contrib.database.fields.handler import FieldHandler
    from jadawel.contrib.database.views.actions import CreateViewSortActionType

    order = args.order.upper()
    if order not in ("ASC", "DESC"):
        raise ValueError("order must be ASC or DESC.")
    view = _get_view(endpoint, args.view_id)
    field = FieldHandler().get_field(args.field_id)
    if field.table_id != view.table_id:
        raise ValueError("That field belongs to a different table.")
    view_sort = CreateViewSortActionType.do(endpoint.user, view, field, order)
    return {"id": view_sort.id, "view_id": view.id, "table_id": view.table_id}


def _describe(doc: str | None) -> str:
    return " ".join((doc or "").split())


def get_app_tools() -> list[SanadTool]:
    """Automation and application-builder tools (``arabase.sanad.app_tools``)."""

    from arabase.sanad import app_tools as t

    return [
        SanadTool(
            "list_applications",
            "List the workspace's applications (databases, builder apps, "
            "automations, dashboards) with their IDs.",
            t.ListApplicationsInput,
            t.list_applications,
        ),
        SanadTool(
            "create_automation",
            "Create an automation. It comes with a first, empty workflow and a "
            "connection to this workspace's tables; add steps to that workflow.",
            t.CreateAutomationInput,
            t.create_automation,
        ),
        SanadTool(
            "create_workflow",
            "Add another workflow to an existing automation.",
            t.CreateWorkflowInput,
            t.create_workflow,
        ),
        SanadTool(
            "describe_automation_step",
            "List the automation step types, or describe one type's settings. "
            "Call it before adding a step whose settings you do not know.",
            t.DescribeAutomationStepInput,
            t.describe_automation_step,
        ),
        SanadTool(
            "get_workflow",
            "Read a workflow: its steps, their settings and how they connect.",
            t.GetWorkflowInput,
            t.get_workflow,
        ),
        SanadTool(
            "get_workflow_runs",
            "Read a workflow's latest runs: whether each succeeded and, if not, "
            "which step failed and why. Use it to check an automation works.",
            t.GetWorkflowRunsInput,
            t.get_workflow_runs,
        ),
        SanadTool(
            "add_automation_step",
            "Add a step to a workflow: first the trigger (no after_step_id), "
            "then each action after the previous step.",
            t.AddAutomationStepInput,
            t.add_automation_step,
        ),
        SanadTool(
            "update_automation_step",
            "Change a step's label or settings.",
            t.UpdateAutomationStepInput,
            t.update_automation_step,
        ),
        SanadTool(
            "delete_automation_step",
            "Delete a workflow step. Needs the user's approval.",
            t.DeleteAutomationStepInput,
            t.delete_automation_step,
        ),
        SanadTool(
            "publish_workflow",
            "Publish a workflow so it runs on real data. Needs the user's "
            "approval; build and review the steps first.",
            t.PublishWorkflowInput,
            t.publish_workflow,
        ),
        SanadTool(
            "create_builder_application",
            "Create an application-builder app (web pages, portals, forms). "
            "It starts with no pages.",
            t.CreateBuilderApplicationInput,
            t.create_builder_application,
        ),
        SanadTool(
            "list_pages",
            "List a builder app's pages and the elements on each.",
            t.ListPagesInput,
            t.list_pages,
        ),
        SanadTool(
            "create_page",
            "Add a page to a builder app.",
            t.CreatePageInput,
            t.create_page,
        ),
        SanadTool(
            "delete_page",
            "Delete a builder page. Needs the user's approval.",
            t.DeletePageInput,
            t.delete_page,
        ),
        SanadTool(
            "add_page_content",
            "Append headings, paragraphs, links (to a page or URL, optionally "
            "as buttons) and images to a page. Give plain text, not formulas.",
            t.AddPageContentInput,
            t.add_page_content,
        ),
        SanadTool(
            "add_table_to_page",
            "Show a database table's rows on a page as a table.",
            t.AddTableToPageInput,
            t.add_table_to_page,
        ),
        SanadTool(
            "add_form_to_page",
            "Add a form to a page; each submission creates a row in a table. "
            "Link-to-table fields become a dropdown of the linked table's rows.",
            t.AddFormToPageInput,
            t.add_form_to_page,
        ),
        SanadTool(
            "add_fields_to_form",
            "Ask for more fields in an existing form, and save them with its "
            "submissions. Link-to-table fields become a dropdown of the linked "
            "table's rows.",
            t.AddFieldsToFormInput,
            t.add_fields_to_form,
        ),
    ]


def get_sanad_tools() -> list[SanadTool]:
    """Every tool Sanad can call, built fresh so registry state is current."""

    from jadawel.core.mcp.registries import mcp_tool_registry

    tools = []
    for name in REUSED_MCP_TOOLS:
        mcp_tool = mcp_tool_registry.get(name)
        tools.append(
            SanadTool(
                name=name,
                description=_describe(mcp_tool.__class__.__doc__),
                input_schema=mcp_tool.input_schema,
                run=mcp_tool._sync_call,
            )
        )
    tools += [
        SanadTool(
            "list_views",
            "List the views (grid, gallery, form, kanban…) of a table.",
            ListViewsInput,
            list_views,
        ),
        SanadTool(
            "create_view",
            "Create a view on a table. Use it to give the user a filtered or "
            "sorted perspective, a gallery, a form, or a kanban board.",
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
    return (
        [
            SanadTool(
                "load_skill",
                "Load a skill: expert instructions for one kind of work. Call it "
                "before you start that work, once per conversation.",
                LoadSkillInput,
                load_skill,
            )
        ]
        + tools
        + get_app_tools()
        + get_page_tools()
        + get_dashboard_tools()
        + get_page_view_tools()
    )


class LoadSkillInput(BaseModel):
    name: str = Field(..., description="The skill's name, from the list of skills.")


def load_skill(endpoint: SanadEndpoint, args: LoadSkillInput) -> dict:
    from arabase.sanad.skills import get_skills

    skill = get_skills().get(args.name)
    if skill is None:
        raise ValueError(
            f"There is no skill {args.name!r}. Skills: {', '.join(get_skills())}."
        )
    return {
        "skill": skill.name,
        "title": skill.title,
        "instructions": skill.instructions,
        "note": "Follow these instructions for the rest of this conversation. "
        "They stay available here; do not load this skill again.",
    }


def get_page_tools() -> list[SanadTool]:
    from arabase.sanad.page_tools import get_page_tools as page_tools

    return page_tools()


def get_dashboard_tools() -> list[SanadTool]:
    from arabase.sanad.dashboard_tools import get_dashboard_tools as dashboard_tools

    return dashboard_tools()


def get_page_view_tools() -> list[SanadTool]:
    from arabase.sanad.page_view_tools import get_page_view_tools as view_tools

    return view_tools()


def safe_tool_error(exc: Exception) -> str:
    """A short error the model can act on, without a traceback."""

    if isinstance(exc, ValidationError):
        return f"Invalid arguments: {exc.errors(include_url=False)}"
    name = exc.__class__.__name__
    message = str(exc).strip()
    if name.endswith("DoesNotExist"):
        return f"{name}: not found or not accessible."
    return f"{name}: {message[:300]}" if message else name
