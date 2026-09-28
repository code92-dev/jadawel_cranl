"""Sanad's skills and the specialist tools they unlock (docs/SANAD_AI_ASSISTANT.md).

The skills are only as good as their facts, so this file also runs the patterns
they teach — a chart grouped by a lookup formula, a loop over every row a
bulk insert created, a detail page read from its page parameter — and checks
the skills name no tool that does not exist.
"""

import re
from decimal import Decimal

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from arabase.sanad.agent import build_agent, build_instructions
from arabase.sanad.skills import get_skills, loaded_skills
from arabase.sanad.tools import APPROVAL_TOOLS, SanadEndpoint, get_sanad_tools
from arabase.sanad.tools.builder_elements import SKILL as PAGE_SKILL
from arabase.sanad.tools.dashboard import SKILL as DASHBOARD_SKILL
from jadawel.contrib.automation.workflows.handler import AutomationWorkflowHandler
from jadawel.contrib.builder.elements.models import Element
from jadawel.contrib.database.rows.handler import RowHandler

SKILL_NAMES = {
    "app-builder",
    "automations",
    "dashboards",
    "formulas",
    "forms",
    "html-pages",
}


def run(tool_name, endpoint, **arguments):
    tool = next(tool for tool in get_sanad_tools() if tool.name == tool_name)
    return tool.call(endpoint, arguments)


@pytest.fixture
def ws(data_fixture):
    user = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    return {
        "user": user,
        "workspace": workspace,
        "database": database,
        "endpoint": SanadEndpoint(user=user, workspace=workspace),
    }


# ---------------------------------------------------------------------------
# The skills themselves
# ---------------------------------------------------------------------------


def test_the_skills_are_there_and_listed_in_the_instructions():
    skills = get_skills()

    assert set(skills) == SKILL_NAMES
    instructions = build_instructions()
    for skill in skills.values():
        assert skill.title and skill.description
        assert len(skill.instructions) > 2000
        assert f"- {skill.name}: {skill.description}" in instructions
        # Only the one-line description is in the prompt, never the body.
        assert skill.instructions[:200] not in instructions


# Words shaped like tool names that the skills use for other things.
NOT_TOOLS = {
    "get_row",
    "list_rows",
    "create_row",
    "update_row",
    "delete_row",
    "get_property",
    "get_single_select_value",
    "get_link_url",
    "get_link_label",
    "get_file_count",
    "get_file_visible_name",
    "get_file_mime_type",
    "get_file_size",
    "get_image_width",
    "get_image_height",
}


def test_skills_name_only_tools_that_exist():
    tool_names = {tool.name for tool in get_sanad_tools()}
    pattern = re.compile(
        r"\b(?:add|create|update|delete|get|list|describe|publish|load)_[a-z_]+\b"
    )
    for skill in get_skills().values():
        named = set(pattern.findall(skill.instructions)) - NOT_TOOLS
        unknown = {name for name in named if not name.startswith("local_")}
        assert unknown <= tool_names, (skill.name, unknown - tool_names)


def test_the_theme_properties_the_app_builder_skill_names_exist():
    from jadawel.contrib.builder.api.theme.serializers import (
        CombinedThemeConfigBlocksRequestSerializer,
    )

    theme = set(CombinedThemeConfigBlocksRequestSerializer().fields)
    text = get_skills()["app-builder"].instructions
    named = set(
        re.findall(
            r"`((?:body|heading_\d|button|link|label|input|table|page|primary|"
            r"secondary|border|main)_[a-z_]+)`",
            text,
        )
    )
    named -= {"page_parameters", "link_name", "input_text"}
    assert named, "the skill should name theme properties"
    assert named <= theme, named - theme
    fonts = set(
        re.findall(r"`([a-z_]+)`", text.split("**Fonts:**")[1].split("- **")[0])
    )
    assert fonts == {
        "inter",
        "arial",
        "verdana",
        "tahoma",
        "trebuchet_ms",
        "times_new_roman",
        "georgia",
        "garamond",
        "courier_new",
        "brush_script_mt",
    }


def test_specialist_tools_belong_to_a_skill_and_deleting_needs_approval():
    tools = {tool.name: tool for tool in get_sanad_tools()}

    for name in ("create_dashboard", "add_dashboard_widget", "get_dashboard"):
        assert tools[name].skill == DASHBOARD_SKILL
    for name in ("add_page_element", "update_app_theme", "add_page_data_source"):
        assert tools[name].skill == PAGE_SKILL
    assert {"delete_page_element", "delete_dashboard_widget"} <= APPROVAL_TOOLS
    # The everyday tools stay available without any skill.
    assert tools["create_table"].skill is None
    assert tools["add_form_to_page"].skill is None


@pytest.mark.django_db
def test_load_skill_returns_the_instructions(ws):
    result = run("load_skill", ws["endpoint"], name="formulas")

    assert result["skill"] == "formulas"
    assert result["instructions"] == get_skills()["formulas"].instructions
    with pytest.raises(ValueError, match="dashboards"):
        run("load_skill", ws["endpoint"], name="cooking")


@pytest.mark.django_db
def test_a_skills_tools_appear_only_after_it_is_loaded(ws):
    from arabase.sanad.agent import SanadDeps

    offered = []

    def respond(messages, info):
        offered.append({tool.name for tool in info.function_tools})
        if len(offered) == 1:
            return ModelResponse(
                parts=[ToolCallPart("load_skill", {"name": "dashboards"}, "c-1")]
            )
        return ModelResponse(parts=[TextPart("ready")])

    agent = build_agent(FunctionModel(respond))
    result = agent.run_sync(
        "build me a dashboard",
        deps=SanadDeps(endpoint=ws["endpoint"], on_action=lambda action: None),
    )

    before, after = offered
    assert "load_skill" in before
    assert "add_dashboard_widget" not in before
    assert "add_page_element" not in before
    assert "add_dashboard_widget" in after
    assert "add_page_element" not in after  # a different skill
    assert loaded_skills(result.all_messages()) == {"dashboards"}


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------


@pytest.fixture
def sales(ws, data_fixture):
    """Deals linked to regions, with an amount, a stage and a close date."""

    database = ws["database"]
    regions = data_fixture.create_database_table(database=database, name="Regions")
    region_name = data_fixture.create_text_field(
        table=regions, name="Region", primary=True
    )
    deals = data_fixture.create_database_table(database=database, name="Deals")
    name = data_fixture.create_text_field(table=deals, name="Deal", primary=True)
    amount = data_fixture.create_number_field(
        table=deals, name="Amount", number_decimal_places=2
    )
    stage = data_fixture.create_single_select_field(table=deals, name="Stage")
    won = data_fixture.create_select_option(field=stage, value="Won", order=0)
    lost = data_fixture.create_select_option(field=stage, value="Lost", order=1)
    close = data_fixture.create_date_field(table=deals, name="Close date")
    region = data_fixture.create_link_row_field(
        table=deals, link_row_table=regions, name="Region"
    )
    # Grouping by a linked record goes through a text formula of its name.
    region_label = data_fixture.create_formula_field(
        table=deals,
        name="Region name",
        formula="join(totext(lookup('Region', 'Region')), ', ')",
    )
    north, south = (
        RowHandler()
        .create_rows(
            ws["user"],
            regions,
            [
                {f"field_{region_name.id}": "North"},
                {f"field_{region_name.id}": "South"},
            ],
        )
        .created_rows
    )
    RowHandler().create_rows(
        ws["user"],
        deals,
        [
            {
                f"field_{name.id}": deal,
                f"field_{amount.id}": value,
                f"field_{stage.id}": option.id,
                f"field_{close.id}": due,
                f"field_{region.id}": [where.id],
            }
            for deal, value, option, due, where in [
                ("A", "100.00", won, "2026-09-28", north),
                ("B", "250.50", won, "2026-10-02", south),
                ("C", "80.00", lost, "2026-09-30", north),
            ]
        ],
    )
    return {
        "table": deals,
        "amount": amount,
        "stage": stage,
        "close": close,
        "name": name,
        "region_label": region_label,
    }


@pytest.mark.django_db
def test_a_dashboard_is_built_widget_by_widget(ws, sales):
    endpoint, table = ws["endpoint"], sales["table"]
    dashboard = run("create_dashboard", endpoint, name="Sales")

    total = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="summary",
        title="Pipeline value",
        width=3,
        height=2,
        appearance={"color": "blue", "icon": "coins", "suffix": "SAR"},
        table_id=table.id,
        field_id=sales["amount"].id,
        aggregation_type="sum",
    )
    by_stage = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="chart",
        title="Value by stage",
        chart_type="doughnut",
        table_id=table.id,
        group_by_field_id=sales["stage"].id,
        series=[
            {"field_id": sales["amount"].id, "aggregation_type": "sum", "label": "SAR"}
        ],
        sort="value_desc",
    )
    by_region = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="chart",
        title="Deals per region",
        chart_type="horizontal_bar",
        table_id=table.id,
        group_by_field_id=sales["region_label"].id,
        series=[{"field_id": sales["name"].id, "aggregation_type": "count"}],
        sort="label_asc",
    )
    target = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="progress",
        title="Quarter target",
        table_id=table.id,
        field_id=sales["amount"].id,
        aggregation_type="sum",
        target_value=1000,
        display_style="ring",
        warning_threshold=40,
        success_threshold=90,
    )
    latest = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="records_list",
        title="Latest deals",
        table_id=table.id,
        field_ids=[sales["name"].id, sales["amount"].id],
        row_count=5,
    )
    due = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="upcoming_dates",
        title="Closing soon",
        table_id=table.id,
        date_field_id=sales["close"].id,
        days_ahead=30,
        include_overdue=True,
        field_ids=[sales["name"].id],
    )
    section = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="text",
        title="المتابعة",
        body="ما يُغلق هذا الشهر.",
        text_style="section",
        width=12,
        height=1,
    )

    assert (total["width"], total["height"]) == (3, 2)
    assert total["settings"]["appearance"] == {
        "color": "blue",
        "icon": "coins",
        "suffix": "SAR",
    }
    assert by_region["settings"]["chart_type"] == "horizontal_bar"
    assert section["settings"]["text_style"] == "section"
    assert section["data"] is None and "shows_now" not in section
    assert Decimal(str(total["shows_now"]["result"])) == Decimal("430.50")
    assert "error" not in by_stage["shows_now"], by_stage["shows_now"]
    assert by_stage["settings"]["chart_type"] == "doughnut"
    assert by_stage["data"]["group_by_field_ids"] == [sales["stage"].id]
    assert "Won" in str(by_stage["shows_now"])
    assert "North" in str(by_region["shows_now"])
    assert "South" in str(by_region["shows_now"])
    assert target["settings"]["display_style"] == "ring"
    assert "error" not in latest["shows_now"], latest["shows_now"]
    assert "error" not in due["shows_now"], due["shows_now"]
    assert due["data"]["days_ahead"] == 30

    changed = run(
        "update_dashboard_widget",
        endpoint,
        widget_id=total["widget_id"],
        title="Won value",
        aggregation_type="max",
        appearance={"compact": True},
    )
    assert changed["title"] == "Won value"
    assert changed["settings"]["appearance"]["color"] == "blue"
    assert changed["settings"]["appearance"]["compact"] is True
    assert Decimal(str(changed["shows_now"]["result"])) == Decimal("250.50")

    run("delete_dashboard_widget", endpoint, widget_id=latest["widget_id"])
    read = run("get_dashboard", endpoint, dashboard_id=dashboard["dashboard_id"])
    assert [w["type"] for w in read["widgets"]] == [
        "summary",
        "chart",
        "chart",
        "progress",
        "upcoming_dates",
        "text",
    ]


@pytest.mark.django_db
def test_widget_mistakes_come_back_as_errors(ws, sales):
    endpoint, table = ws["endpoint"], sales["table"]
    dashboard = run("create_dashboard", endpoint, name="Sales")

    with pytest.raises(Exception, match="compatible|aggregation"):
        run(
            "add_dashboard_widget",
            endpoint,
            dashboard_id=dashboard["dashboard_id"],
            type="summary",
            title="Sum of names",
            table_id=table.id,
            field_id=sales["name"].id,
            aggregation_type="sum",
        )


@pytest.mark.django_db
def test_a_widget_is_set_up_in_one_call(ws, sales):
    """A live model once created bare widgets and patched them setting by
    setting until it ran out of steps; an incomplete widget is now refused."""

    dashboard = run("create_dashboard", ws["endpoint"], name="Sales")

    with pytest.raises(ValueError, match="field_id, aggregation_type"):
        run(
            "add_dashboard_widget",
            ws["endpoint"],
            dashboard_id=dashboard["dashboard_id"],
            type="summary",
            title="Pipeline",
            table_id=sales["table"].id,
        )
    with pytest.raises(ValueError, match="needs table_id"):
        run(
            "add_dashboard_widget",
            ws["endpoint"],
            dashboard_id=dashboard["dashboard_id"],
            type="summary",
            title="Pipeline",
            field_id=sales["amount"].id,
            aggregation_type="sum",
        )
    with pytest.raises(ValueError, match="group_by_field_id, series"):
        run(
            "add_dashboard_widget",
            ws["endpoint"],
            dashboard_id=dashboard["dashboard_id"],
            type="chart",
            title="By stage",
            table_id=sales["table"].id,
        )
    assert (
        run("get_dashboard", ws["endpoint"], dashboard_id=dashboard["dashboard_id"])[
            "widgets"
        ]
        == []
    )


@pytest.mark.django_db
def test_dashboard_tools_stay_in_the_chat_workspace(ws, data_fixture):
    other = data_fixture.create_user()
    theirs = data_fixture.create_workspace(user=other)
    data_fixture.create_user_workspace(workspace=theirs, user=ws["user"])
    dashboard = run(
        "create_dashboard", SanadEndpoint(user=other, workspace=theirs), name="X"
    )

    with pytest.raises(Exception):
        run("get_dashboard", ws["endpoint"], dashboard_id=dashboard["dashboard_id"])


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_designed_list_and_detail_app(ws, data_fixture):
    endpoint = ws["endpoint"]
    table = data_fixture.create_database_table(database=ws["database"], name="Items")
    title = data_fixture.create_text_field(table=table, name="Title", primary=True)
    app = run("create_builder_application", endpoint, name="Catalogue")
    home = run(
        "create_page",
        endpoint,
        application_id=app["application_id"],
        name="Home",
        path="/",
    )
    detail = run(
        "create_page",
        endpoint,
        application_id=app["application_id"],
        name="Item",
        path="/item/:id",
    )
    assert detail["read_parameters_with"] == ["get('page_parameter.id')"]

    theme = run(
        "update_app_theme",
        endpoint,
        application_id=app["application_id"],
        settings={"primary_color": "#0f766eff", "body_font_family": "tahoma"},
    )
    assert theme["updated"] == ["body_font_family", "primary_color"]
    with pytest.raises(ValueError, match="Unknown theme"):
        run(
            "update_app_theme",
            endpoint,
            application_id=app["application_id"],
            settings={"primary_colour": "#000000"},
        )

    header = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="header",
        settings={"share_type": "all"},
    )
    heading = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="heading",
        settings={"value": "Our catalogue", "level": 1},
        parent_element_id=header["id"],
    )
    menu = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="menu",
        settings={
            "orientation": "horizontal",
            "menu_items": [
                {
                    "type": "link",
                    "name": "'Home'",  # quoted like a formula, as a model did
                    "navigation_type": "page",
                    "navigate_to_page_id": home["page_id"],
                },
                {
                    "type": "link",
                    "name": "Contact",
                    "variant": "button",
                    "navigation_type": "custom",
                    "navigate_to_url": "'https://example.com'",
                    "target": "blank",
                },
            ],
        },
        parent_element_id=header["id"],
    )
    assert [item["name"] for item in menu["settings"]["menu_items"]] == [
        "Home",
        "Contact",
    ]
    columns = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="column",
        settings={
            "column_amount": 2,
            "style_background": "color",
            "style_background_color": "primary",
        },
    )
    left = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="text",
        settings={"value": "Browse everything we have."},
        parent_element_id=columns["id"],
        place_in_container='"1"',  # as a live model once sent it
    )
    right = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="text",
        settings={"value": "Or search."},
        parent_element_id=columns["id"],
        place_in_container=0,
    )
    assert right["place_in_container"] == "0"
    # Updating and deleting run inside a transaction, as the editor's API does.
    styled = run(
        "update_page_element",
        endpoint,
        element_id=columns["id"],
        settings={"column_gap": 24, "style_padding_top": 32},
    )
    assert styled["settings"]["column_gap"] == 24
    # The styles set are visible in the result; untouched ones are not listed.
    assert styled["styles"]["style_padding_top"] == 32
    assert columns["styles"]["style_background"] == "color"
    assert "style_margin_top" not in styled["styles"]
    run("delete_page_element", endpoint, element_id=right["id"])
    assert not Element.objects.filter(id=right["id"]).exists()
    items = run(
        "add_page_data_source",
        endpoint,
        page_id=home["page_id"],
        name="Items",
        kind="list_rows",
        table_id=table.id,
    )
    repeat = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="repeat",
        settings={
            "data_source_id": items["data_source_id"],
            "items_per_page": 12,
            "orientation": "horizontal",
            "items_per_row": {"desktop": 3, "tablet": 2, "smartphone": 1},
            "horizontal_gap": 16,
            "vertical_gap": 16,
        },
    )
    # The table link column exactly as the skill writes it.
    table_element = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="table",
        settings={
            "data_source_id": items["data_source_id"],
            "items_per_page": 20,
            "fields": [
                {
                    "name": "Title",
                    "type": "text",
                    "value": f"get('current_record.field_{title.id}')",
                },
                {
                    "name": "Open",
                    "type": "link",
                    "link_name": "'Open'",
                    "variant": "button",
                    "navigation_type": "page",
                    "navigate_to_page_id": detail["page_id"],
                    "page_parameters": [
                        {"name": "id", "value": "get('current_record.id')"}
                    ],
                },
            ],
        },
    )
    assert [f["type"] for f in table_element["settings"]["fields"]] == [
        "text",
        "link",
    ]
    card_link = run(
        "add_page_element",
        endpoint,
        page_id=home["page_id"],
        type="link",
        settings={
            "value": f"get('current_record.field_{title.id}')",
            "variant": "button",
            "navigation_type": "page",
            "navigate_to_page_id": detail["page_id"],
            "page_parameters": [{"name": "id", "value": "get('current_record.id')"}],
        },
        parent_element_id=repeat["id"],
    )
    one = run(
        "add_page_data_source",
        endpoint,
        page_id=detail["page_id"],
        name="Item",
        kind="get_row",
        table_id=table.id,
        row_id="get('page_parameter.id')",
    )
    run(
        "add_page_element",
        endpoint,
        page_id=detail["page_id"],
        type="heading",
        settings={
            "value": f"get('data_source.{one['data_source_id']}.field_{title.id}')"
        },
    )

    # Plain text was taken literally, formulas were kept as formulas.
    assert Element.objects.get(id=heading["id"]).specific.value["formula"] == (
        "'Our catalogue'"
    )
    assert left["place_in_container"] == "1"
    assert header["page_id"] != home["page_id"]  # on the shared page
    assert card_link["settings"]["variant"] == "button"
    listed = run("list_page_elements", endpoint, page_id=home["page_id"])
    assert {e["type"] for e in listed["elements"]} >= {"column", "text", "repeat"}
    assert [e["type"] for e in listed["shared_elements"]][:1] == ["header"]
    assert [ds["name"] for ds in listed["data_sources"]] == ["Items"]
    described = run("describe_page_element", endpoint, type="repeat")
    assert "data_source_id" in described["settings"]


# ---------------------------------------------------------------------------
# Automations: every row of a bulk insert, through an iterator
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_an_iterator_handles_every_row_a_bulk_insert_creates(ws, data_fixture):
    endpoint = ws["endpoint"]
    orders = data_fixture.create_database_table(database=ws["database"], name="Orders")
    ref = data_fixture.create_text_field(table=orders, name="Ref", primary=True)
    log = data_fixture.create_database_table(database=ws["database"], name="Log")
    note = data_fixture.create_text_field(table=log, name="Note", primary=True)

    automation = run("create_automation", endpoint, name="Log orders")
    trigger = run(
        "add_automation_step",
        endpoint,
        workflow_id=automation["workflow_id"],
        type="local_jadawel_rows_created",
        settings={"table_id": orders.id},
    )
    loop = run(
        "add_automation_step",
        endpoint,
        workflow_id=automation["workflow_id"],
        type="iterator",
        after_step_id=trigger["id"],
        settings={"source": f"get('previous_node.{trigger['id']}')"},
    )
    run(
        "add_automation_step",
        endpoint,
        workflow_id=automation["workflow_id"],
        type="local_jadawel_create_row",
        inside_step_id=loop["id"],
        settings={
            "table_id": log.id,
            "field_mappings": [
                {
                    "field_id": note.id,
                    "enabled": True,
                    "value": "concat('Order ', "
                    f"get('current_iteration.{loop['id']}.item.Ref'))",
                }
            ],
        },
    )
    run("publish_workflow", endpoint, workflow_id=automation["workflow_id"])
    workflow = AutomationWorkflowHandler().get_workflow(automation["workflow_id"])
    assert AutomationWorkflowHandler().get_published_workflow(workflow) is not None

    RowHandler().create_rows(
        ws["user"], orders, [{f"field_{ref.id}": r} for r in ("A1", "A2", "A3")]
    )

    notes = sorted(
        getattr(row, f"field_{note.id}") for row in log.get_model().objects.all()
    )
    assert notes == ["Order A1", "Order A2", "Order A3"]


@pytest.mark.django_db(transaction=True)
def test_a_router_sends_each_row_down_its_branch(ws, data_fixture):
    endpoint = ws["endpoint"]
    tickets = data_fixture.create_database_table(database=ws["database"], name="T")
    subject = data_fixture.create_text_field(
        table=tickets, name="Subject", primary=True
    )
    priority = data_fixture.create_number_field(table=tickets, name="Priority")
    log = data_fixture.create_database_table(database=ws["database"], name="Log")
    note = data_fixture.create_text_field(table=log, name="Note", primary=True)

    automation = run("create_automation", endpoint, name="Triage")
    trigger = run(
        "add_automation_step",
        endpoint,
        workflow_id=automation["workflow_id"],
        type="local_jadawel_rows_created",
        settings={"table_id": tickets.id},
    )
    router = run(
        "add_automation_step",
        endpoint,
        workflow_id=automation["workflow_id"],
        type="router",
        after_step_id=trigger["id"],
        settings={
            "default_edge_label": "Normal",
            "edges": [
                {
                    "label": "Urgent",
                    "condition": f"get('previous_node.{trigger['id']}.0."
                    f"field_{priority.id}') > 3",
                }
            ],
        },
    )
    [urgent] = router["settings"]["edges"]
    assert urgent["uid"]
    # Changing a branch by label keeps its uid, so attached steps stay attached.
    renamed = run(
        "update_automation_step",
        endpoint,
        step_id=router["id"],
        settings={"edges": [{"label": "Urgent", "condition": urgent["condition"]}]},
    )
    assert renamed["settings"]["edges"][0]["uid"] == urgent["uid"]

    def log_step(branch, text):
        run(
            "add_automation_step",
            endpoint,
            workflow_id=automation["workflow_id"],
            type="local_jadawel_create_row",
            after_step_id=router["id"],
            branch=branch,
            settings={
                "table_id": log.id,
                "field_mappings": [
                    {"field_id": note.id, "enabled": True, "value": f"'{text}'"}
                ],
            },
        )

    log_step(urgent["uid"], "urgent")
    log_step(None, "normal")
    run("publish_workflow", endpoint, workflow_id=automation["workflow_id"])

    RowHandler().create_rows(
        ws["user"], tickets, [{f"field_{subject.id}": "a", f"field_{priority.id}": 5}]
    )
    RowHandler().create_rows(
        ws["user"], tickets, [{f"field_{subject.id}": "b", f"field_{priority.id}": 1}]
    )

    notes = sorted(
        getattr(row, f"field_{note.id}") for row in log.get_model().objects.all()
    )
    assert notes == ["normal", "urgent"]


@pytest.mark.django_db
def test_the_dashboard_skills_techniques_work(ws, sales, data_fixture):
    """Month buckets, a rate from a boolean formula, a median — and linked
    records only through a formula, as the skill says."""

    endpoint, table = ws["endpoint"], sales["table"]
    month = data_fixture.create_formula_field(
        table=table,
        name="Month",
        formula="datetime_format(field('Close date'), 'YYYY-MM')",
    )
    is_won = data_fixture.create_formula_field(
        table=table, name="Is won", formula="totext(field('Stage')) = 'Won'"
    )
    dashboard = run("create_dashboard", endpoint, name="Techniques")

    trend = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="chart",
        title="Value per month",
        chart_type="line",
        table_id=table.id,
        group_by_field_id=month.id,
        sort="label_asc",
        series=[{"field_id": sales["amount"].id, "aggregation_type": "sum"}],
    )
    win_rate = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="summary",
        title="Win rate",
        table_id=table.id,
        field_id=is_won.id,
        aggregation_type="checked_percentage",
    )
    median = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="summary",
        title="Median deal",
        table_id=table.id,
        field_id=sales["amount"].id,
        aggregation_type="median",
    )

    assert "2026-09" in str(trend["shows_now"]) and "2026-10" in str(trend["shows_now"])
    assert str(trend["shows_now"]).index("2026-09") < str(trend["shows_now"]).index(
        "2026-10"
    )
    assert round(win_rate["shows_now"]["result"], 1) == 66.7
    assert Decimal(str(median["shows_now"]["result"])) == Decimal("100")

    linked = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="chart",
        title="Straight by link",
        table_id=table.id,
        group_by_field_id=table.field_set.get(name="Region").id,
        series=[{"field_id": sales["name"].id, "aggregation_type": "count"}],
    )
    # A linked field groups by row IDs — why the skill groups by a name formula.
    assert [g["value"] for g in linked["shows_now"]["result"]["groups"]] == ["1", "2"]


@pytest.mark.django_db
def test_select_filters_take_the_option_text(ws, sales):
    """A live model filtered a view with stage 'Open' (the text); stored as-is
    that matched nothing, so it told the user filters are ignored."""

    endpoint, table = ws["endpoint"], sales["table"]
    view = run("create_view", endpoint, table_id=table.id, name="Won deals")
    run(
        "add_view_filter",
        endpoint,
        view_id=view["id"],
        field_id=sales["stage"].id,
        type="single_select_equal",
        value="won",
    )
    with pytest.raises(ValueError, match="Won, Lost"):
        run(
            "add_view_filter",
            endpoint,
            view_id=view["id"],
            field_id=sales["stage"].id,
            type="single_select_equal",
            value="Pending",
        )

    dashboard = run("create_dashboard", endpoint, name="Sales")
    won = run(
        "add_dashboard_widget",
        endpoint,
        dashboard_id=dashboard["dashboard_id"],
        type="summary",
        title="Won value",
        table_id=table.id,
        view_id=view["id"],
        field_id=sales["amount"].id,
        aggregation_type="sum",
    )
    # 100.00 + 250.50 won; the lost 80.00 is filtered out.
    assert Decimal(str(won["shows_now"]["result"])) == Decimal("350.50")
