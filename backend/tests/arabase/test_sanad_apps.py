"""Sanad building automations and application-builder apps.

The first half calls the tools directly and asserts what they persisted. The
second half drives a whole chat turn with a scripted model and then uses the
result for real: the published workflow fires on a new row, and the generated
form's submit action creates a row.
"""

import json
from unittest.mock import patch

from django.shortcuts import reverse

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED

from arabase.sanad import runner
from arabase.sanad.models import SanadMessage, SanadMessageStatus
from arabase.sanad.tools import APPROVAL_TOOLS, SanadEndpoint, get_sanad_tools
from jadawel.contrib.automation.models import Automation, AutomationWorkflow
from jadawel.contrib.automation.nodes.models import AutomationNode
from jadawel.contrib.automation.workflows.handler import AutomationWorkflowHandler
from jadawel.contrib.builder.data_sources.models import DataSource
from jadawel.contrib.builder.elements.models import (
    ChoiceElement,
    Element,
    FormContainerElement,
    HeadingElement,
    LinkElement,
    TableElement,
    TextElement,
)
from jadawel.contrib.builder.models import Builder
from jadawel.contrib.builder.pages.models import Page
from jadawel.contrib.builder.workflow_actions.models import BuilderWorkflowAction
from jadawel.contrib.database.rows.handler import RowHandler
from jadawel.core.integrations.models import Integration

MODEL = "openai/test-model"


@pytest.fixture(autouse=True)
def turns_run_inline(monkeypatch):
    """Run each turn inside the request, so a test can assert on its outcome."""

    monkeypatch.setattr(runner, "RUN_INLINE", True)


@pytest.fixture
def ws(data_fixture):
    """A staff member's workspace with a Customers table."""

    user, token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database, name="Customers")
    name = data_fixture.create_text_field(table=table, name="Name", primary=True)
    age = data_fixture.create_number_field(table=table, name="Age")
    vip = data_fixture.create_boolean_field(table=table, name="VIP")
    tier = data_fixture.create_single_select_field(table=table, name="Tier")
    data_fixture.create_select_option(field=tier, value="Gold", order=0)
    data_fixture.create_select_option(field=tier, value="Silver", order=1)
    return {
        "user": user,
        "token": token,
        "workspace": workspace,
        "table": table,
        "fields": {"name": name, "age": age, "vip": vip, "tier": tier},
        "endpoint": SanadEndpoint(user=user, workspace=workspace),
    }


def run(tool_name, endpoint, **arguments):
    tool = next(tool for tool in get_sanad_tools() if tool.name == tool_name)
    return tool.call(endpoint, arguments)


# ---------------------------------------------------------------------------
# Automation tools
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_automation_comes_with_a_workflow_and_a_connection(ws):
    result = run(
        "create_automation", ws["endpoint"], name="المتابعة", workflow_name="عميل جديد"
    )

    automation = Automation.objects.get(id=result["automation_id"])
    assert automation.workspace_id == ws["workspace"].id
    assert result["name"] == "المتابعة"
    workflow = AutomationWorkflow.objects.get(id=result["workflow_id"])
    assert workflow.automation_id == automation.id
    assert workflow.name == "عميل جديد"
    integration = Integration.objects.get(id=result["integration_id"])
    assert integration.get_type().type == "local_jadawel"


@pytest.mark.django_db
def test_steps_are_created_with_validated_settings(ws, data_fixture):
    target = data_fixture.create_database_table(
        database=ws["table"].database, name="Log"
    )
    note = data_fixture.create_text_field(table=target, name="Note", primary=True)
    created = run("create_automation", ws["endpoint"], name="Log")
    name_id = ws["fields"]["name"].id

    trigger = run(
        "add_automation_step",
        ws["endpoint"],
        workflow_id=created["workflow_id"],
        type="local_jadawel_rows_created",
        label="New customer",
        settings={"table_id": ws["table"].id},
    )
    action = run(
        "add_automation_step",
        ws["endpoint"],
        workflow_id=created["workflow_id"],
        type="local_jadawel_create_row",
        after_step_id=trigger["id"],
        settings={
            "table_id": target.id,
            "field_mappings": [
                {
                    "field_id": note.id,
                    "enabled": True,
                    "value": f"concat('New: ', get('previous_node.{trigger['id']}.0.field_{name_id}'))",
                }
            ],
        },
    )

    assert trigger["label"] == "New customer"
    assert trigger["settings"]["table_id"] == ws["table"].id
    assert trigger["settings"]["integration_id"] == created["integration_id"]
    assert action["settings"]["table_id"] == target.id
    workflow = run("get_workflow", ws["endpoint"], workflow_id=created["workflow_id"])
    assert [step["type"] for step in workflow["steps"]] == [
        "local_jadawel_rows_created",
        "local_jadawel_create_row",
    ]
    assert workflow["graph"]["0"] == trigger["id"]
    assert workflow["graph"][str(trigger["id"])]["next"] == {"": [action["id"]]}
    mapping = workflow["steps"][1]["settings"]["field_mappings"][0]
    assert mapping["field_id"] == note.id
    assert "previous_node" in mapping["value"]["formula"]
    assert "schema" not in workflow["steps"][0]["settings"]


def build_copy_workflow(ws, data_fixture, value_for_tier):
    """New customer -> a row in Leads, whose Tier select is set from a formula."""

    leads = data_fixture.create_database_table(
        database=ws["table"].database, name="Leads"
    )
    data_fixture.create_text_field(table=leads, name="Lead", primary=True)
    tier = data_fixture.create_single_select_field(table=leads, name="Tier")
    data_fixture.create_select_option(field=tier, value="High", order=0)
    data_fixture.create_select_option(field=tier, value="Low", order=1)
    created = run("create_automation", ws["endpoint"], name="Leads")
    trigger = run(
        "add_automation_step",
        ws["endpoint"],
        workflow_id=created["workflow_id"],
        type="local_jadawel_rows_created",
        settings={"table_id": ws["table"].id},
    )
    action = run(
        "add_automation_step",
        ws["endpoint"],
        workflow_id=created["workflow_id"],
        type="local_jadawel_create_row",
        after_step_id=trigger["id"],
        settings={
            "table_id": leads.id,
            "field_mappings": [
                {
                    "field_id": tier.id,
                    "enabled": True,
                    "value": value_for_tier(trigger["id"]),
                }
            ],
        },
    )
    return created, action, leads, tier


@pytest.mark.django_db
def test_step_results_name_the_field_behind_each_mapping(ws, data_fixture):
    _, action, _, tier = build_copy_workflow(ws, data_fixture, lambda _: "'High'")

    [mapping] = action["settings"]["field_mappings"]
    assert mapping["field_id"] == tier.id
    assert mapping["field_name"] == "Tier"
    assert mapping["field_type"] == "single_select"
    assert mapping["select_options"] == ["High", "Low"]


@pytest.mark.django_db(transaction=True)
def test_workflow_runs_report_why_a_step_failed(ws, data_fixture):
    """The mistake a live chat made: a select field given the new row's ID."""

    created, _, leads, _ = build_copy_workflow(
        ws, data_fixture, lambda trigger_id: f"get('previous_node.{trigger_id}.0.id')"
    )
    run("publish_workflow", ws["endpoint"], workflow_id=created["workflow_id"])
    assert (
        run("get_workflow_runs", ws["endpoint"], workflow_id=created["workflow_id"])[
            "runs"
        ]
        == []
    )

    name_id = ws["fields"]["name"].id
    RowHandler().create_rows(ws["user"], ws["table"], [{f"field_{name_id}": "Noura"}])

    runs = run("get_workflow_runs", ws["endpoint"], workflow_id=created["workflow_id"])
    [latest] = runs["runs"]
    assert latest["status"] == "error"
    assert "Tier" in latest["error"]
    assert "not a valid select option" in latest["error"]
    failed = [step for step in latest["steps"] if step["status"] == "error"]
    assert [step["type"] for step in failed] == ["local_jadawel_create_row"]
    assert leads.get_model().objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_workflow_runs_show_a_successful_run(ws, data_fixture):
    created, _, leads, tier = build_copy_workflow(ws, data_fixture, lambda _: "'High'")
    run("publish_workflow", ws["endpoint"], workflow_id=created["workflow_id"])
    name_id = ws["fields"]["name"].id
    RowHandler().create_rows(ws["user"], ws["table"], [{f"field_{name_id}": "Noura"}])

    [latest] = run(
        "get_workflow_runs", ws["endpoint"], workflow_id=created["workflow_id"]
    )["runs"]
    assert latest["status"] == "success"
    assert latest["error"] == ""
    [lead] = leads.get_model().objects.all()
    assert getattr(lead, f"field_{tier.id}").value == "High"


@pytest.mark.django_db
def test_invalid_step_settings_are_rejected_like_the_editor_does(ws):
    created = run("create_automation", ws["endpoint"], name="Schedule")

    with pytest.raises(Exception) as error:
        run(
            "add_automation_step",
            ws["endpoint"],
            workflow_id=created["workflow_id"],
            type="periodic",
            settings={"interval": "FORTNIGHTLY"},
        )

    assert "interval" in str(error.value.args) or "interval" in str(
        getattr(error.value, "detail", "")
    )
    # The step and its half-applied settings were rolled back together.
    assert not AutomationNode.objects.filter(
        workflow_id=created["workflow_id"]
    ).exists()


@pytest.mark.django_db
def test_describe_automation_step_reads_the_real_schema(ws):
    catalogue = run("describe_automation_step", ws["endpoint"])
    types = {item["type"]: item for item in catalogue["step_types"]}
    assert types["periodic"]["trigger"] is True
    assert types["local_jadawel_create_row"]["trigger"] is False

    periodic = run("describe_automation_step", ws["endpoint"], type="periodic")
    assert periodic["settings"]["interval"]["type"] == "choice"
    assert "DAY" in periodic["settings"]["interval"]["choices"]
    create_row = run(
        "describe_automation_step", ws["endpoint"], type="local_jadawel_create_row"
    )
    assert create_row["needs_connection"] == "local_jadawel"
    assert create_row["settings"]["field_mappings"]["type"] == "list"
    assert "value" in create_row["settings"]["field_mappings"]["item"]


@pytest.mark.django_db
def test_automation_tools_stay_in_the_chat_workspace(ws, data_fixture):
    other_user = data_fixture.create_user(is_staff=True)
    other_workspace = data_fixture.create_workspace(user=other_user)
    foreign = run(
        "create_automation",
        SanadEndpoint(user=other_user, workspace=other_workspace),
        name="Theirs",
    )
    # The chat user is made a member of the other workspace too: permissions
    # alone would allow it, so this proves the workspace scope itself.
    data_fixture.create_user_workspace(workspace=other_workspace, user=ws["user"])

    for tool, arguments in [
        ("get_workflow", {"workflow_id": foreign["workflow_id"]}),
        ("get_workflow_runs", {"workflow_id": foreign["workflow_id"]}),
        (
            "add_automation_step",
            {"workflow_id": foreign["workflow_id"], "type": "periodic"},
        ),
        ("create_workflow", {"automation_id": foreign["automation_id"], "name": "x"}),
        ("list_pages", {"application_id": foreign["automation_id"]}),
    ]:
        with pytest.raises(Exception):
            run(tool, ws["endpoint"], **arguments)
    assert not AutomationNode.objects.exists()


@pytest.mark.django_db
def test_publishing_and_deleting_need_approval():
    names = {tool.name for tool in get_sanad_tools()}
    assert {
        "publish_workflow",
        "delete_automation_step",
        "delete_page",
    } <= APPROVAL_TOOLS
    assert APPROVAL_TOOLS <= names
    assert {name for name in names if name.startswith("delete_")} <= APPROVAL_TOOLS


# ---------------------------------------------------------------------------
# Builder tools
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_builder_application_starts_empty_with_a_connection(ws):
    result = run("create_builder_application", ws["endpoint"], name="بوابة العملاء")

    builder = Builder.objects.get(id=result["application_id"])
    assert builder.name == "بوابة العملاء"
    assert list(Page.objects.filter(builder=builder, shared=False)) == []
    assert Integration.objects.get(id=result["integration_id"]).application_id == (
        builder.id
    )
    listed = run("list_applications", ws["endpoint"], type="builder")
    assert listed == [{"id": builder.id, "name": "بوابة العملاء", "type": "builder"}]


@pytest.mark.django_db
def test_pages_get_content_from_plain_text(ws):
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    home = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="Home",
        path="/",
    )
    about = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="About",
        path="about",
    )
    assert about["path"] == "/about"

    run(
        "add_page_content",
        ws["endpoint"],
        page_id=home["page_id"],
        elements=[
            {"type": "heading", "text": "It's our portal", "level": 1},
            {"type": "text", "text": "**Welcome**", "markdown": True},
            {"type": "link", "text": "About us", "to_page_id": about["page_id"]},
            {
                "type": "link",
                "text": "Website",
                "url": "https://jadawl.site",
                "as_button": True,
            },
            {"type": "image", "text": "Logo", "url": "https://jadawl.site/logo.png"},
        ],
    )

    heading = HeadingElement.objects.get(page_id=home["page_id"])
    assert heading.value["formula"] == "'It\\'s our portal'"
    assert heading.level == 1
    assert TextElement.objects.get(page_id=home["page_id"]).format == "markdown"
    page_link, url_link = LinkElement.objects.filter(page_id=home["page_id"]).order_by(
        "order"
    )
    assert page_link.navigate_to_page_id == about["page_id"]
    assert url_link.variant == "button"
    assert url_link.navigate_to_url["formula"] == "'https://jadawl.site'"
    pages = run("list_pages", ws["endpoint"], application_id=app["application_id"])
    assert [page["name"] for page in pages] == ["Home", "About"]
    assert [element["type"] for element in pages[0]["elements"]] == [
        "heading",
        "text",
        "link",
        "link",
        "image",
    ]


@pytest.mark.django_db
def test_a_table_element_lists_a_tables_rows(ws):
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    page = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="Customers",
        path="/customers",
    )
    fields = ws["fields"]

    result = run(
        "add_table_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=ws["table"].id,
        field_ids=[fields["name"].id, fields["tier"].id, fields["vip"].id],
        title="العملاء",
    )

    data_source = DataSource.objects.get(id=result["data_source_id"])
    assert data_source.service.specific.table_id == ws["table"].id
    element = TableElement.objects.get(id=result["table_element_id"])
    columns = {
        column.name: (column.type, column.config) for column in element.fields.all()
    }
    tier_type, tier_config = columns["Tier"]
    assert tier_type == "text"
    assert tier_config["value"]["formula"].endswith(".value')")
    assert columns["VIP"][0] == "boolean"
    assert result["columns"] == ["Name", "Tier", "VIP"]


@pytest.mark.django_db
def test_a_form_maps_each_field_to_a_fitting_input(ws, data_fixture):
    data_fixture.create_formula_field(
        table=ws["table"], name="Label", formula="field('Name')"
    )
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    page = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="Join",
        path="/join",
    )

    result = run(
        "add_form_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=ws["table"].id,
        required_field_ids=[ws["fields"]["name"].id],
        submit_label="انضم",
        success_message="شكرًا",
    )

    assert [item["field"] for item in result["inputs"]] == [
        "Name",
        "Age",
        "VIP",
        "Tier",
    ]
    assert result["skipped_fields"] == []  # the formula field is read-only
    form = FormContainerElement.objects.get(id=result["form_element_id"])
    children = Element.objects.filter(parent_element=form).order_by("order")
    assert [child.get_type().type for child in children] == [
        "input_text",
        "input_text",
        "checkbox",
        "choice",
    ]
    assert children[0].specific.required is True
    assert children[1].specific.validation_type == "integer"
    choice = ChoiceElement.objects.get(parent_element=form)
    assert [option.value for option in choice.choiceelementoption_set.all()] == [
        "Gold",
        "Silver",
    ]
    actions = BuilderWorkflowAction.objects.filter(element=form).order_by("order")
    assert [action.get_type().type for action in actions] == [
        "create_row",
        "notification",
    ]


@pytest.mark.django_db
def test_builder_tools_reject_the_wrong_application_type(ws):
    automation = run("create_automation", ws["endpoint"], name="Not an app")

    with pytest.raises(ValueError, match="is a automation, not a builder"):
        run(
            "create_page",
            ws["endpoint"],
            application_id=automation["automation_id"],
            name="x",
            path="/x",
        )


# ---------------------------------------------------------------------------
# Whole turns
# ---------------------------------------------------------------------------


def scripted(steps):
    """Each step is a callable(tool_results) returning the model's response."""

    remaining = list(steps)
    results = []

    def respond(messages, info):
        for part in messages[-1].parts:
            if part.part_kind == "tool-return":
                results.append(part.content)
        step = remaining.pop(0)
        return step(results)

    return FunctionModel(respond)


def call(name, arguments, call_id=None):
    return ModelResponse(
        parts=[ToolCallPart(name, arguments, tool_call_id=call_id or f"c-{name}")]
    )


def say(text):
    return lambda results: ModelResponse(parts=[TextPart(text)])


def post_message(api_client, ws, chat_id, content, model):
    with (
        patch("arabase.sanad.agent.get_available_models", return_value=[MODEL]),
        patch("arabase.sanad.agent.build_ai_model", return_value=model),
    ):
        return api_client.post(
            reverse("api:arabase:sanad_messages", kwargs={"chat_id": chat_id}),
            {"content": content},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {ws['token']}",
        )


def new_chat(api_client, ws):
    response = api_client.post(
        reverse("api:arabase:sanad_chats", kwargs={"workspace_id": ws["workspace"].id}),
        HTTP_AUTHORIZATION=f"JWT {ws['token']}",
    )
    return response.json()["id"]


@pytest.mark.django_db(transaction=True)
def test_a_chat_builds_and_publishes_a_working_automation(api_client, data_fixture, ws):
    table = ws["table"]
    name_id = ws["fields"]["name"].id
    log = data_fixture.create_database_table(database=table.database, name="Log")
    note = data_fixture.create_text_field(table=log, name="Note", primary=True)
    chat_id = new_chat(api_client, ws)

    model = scripted(
        [
            lambda r: call("create_automation", {"name": "Welcome"}),
            lambda r: call(
                "add_automation_step",
                {
                    "workflow_id": r[-1]["workflow_id"],
                    "type": "local_jadawel_rows_created",
                    "settings": {"table_id": table.id},
                },
            ),
            lambda r: call(
                "add_automation_step",
                {
                    "workflow_id": r[-1]["workflow_id"],
                    "type": "local_jadawel_create_row",
                    "after_step_id": r[-1]["id"],
                    "settings": {
                        "table_id": log.id,
                        "field_mappings": [
                            {
                                "field_id": note.id,
                                "enabled": True,
                                "value": "concat('Welcome ', get('previous_node."
                                f"{r[-1]['id']}.0.field_{name_id}'))",
                            }
                        ],
                    },
                },
            ),
            lambda r: call(
                "publish_workflow", {"workflow_id": r[-1]["workflow_id"]}, "c-publish"
            ),
            say("Your automation is live."),
        ]
    )

    post_message(api_client, ws, chat_id, "Log every new customer", model)

    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.AWAITING_APPROVAL
    assert reply.approvals[0]["tool"] == "publish_workflow"
    workflow = AutomationWorkflow.objects.get()
    assert AutomationWorkflowHandler().get_published_workflow(workflow) is None
    assert [a["refs"].get("automation_id") for a in reply.actions][:1] == [
        workflow.automation_id
    ]

    with patch("arabase.sanad.agent.build_ai_model", return_value=model):
        response = api_client.post(
            reverse("api:arabase:sanad_decisions", kwargs={"chat_id": chat_id}),
            {"decisions": [{"tool_call_id": "c-publish", "approved": True}]},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {ws['token']}",
        )
    assert response.status_code == HTTP_202_ACCEPTED
    reply.refresh_from_db()
    assert reply.status == SanadMessageStatus.DONE
    published = AutomationWorkflowHandler().get_published_workflow(
        workflow, with_cache=False
    )
    assert published is not None and published.state == "live"

    # The published workflow really runs: a new customer produces a log row.
    RowHandler().create_rows(ws["user"], table, [{f"field_{name_id}": "Noura"}])
    notes = [getattr(row, f"field_{note.id}") for row in log.get_model().objects.all()]
    assert "Welcome Noura" in notes


@pytest.mark.django_db(transaction=True)
def test_a_chat_builds_a_portal_whose_form_saves_rows(api_client, ws):
    table = ws["table"]
    fields = ws["fields"]
    chat_id = new_chat(api_client, ws)
    model = scripted(
        [
            lambda r: call("create_builder_application", {"name": "Portal"}),
            lambda r: call(
                "create_page",
                {
                    "application_id": r[-1]["application_id"],
                    "name": "Join",
                    "path": "/",
                },
            ),
            lambda r: call(
                "add_form_to_page",
                {
                    "page_id": r[-1]["page_id"],
                    "table_id": table.id,
                    "field_ids": [fields["name"].id, fields["tier"].id],
                },
            ),
            say("Your portal is ready to preview."),
        ]
    )

    post_message(api_client, ws, chat_id, "Build a join form", model)

    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.DONE, reply.error
    assert [action["tool"] for action in reply.actions] == [
        "create_builder_application",
        "create_page",
        "add_form_to_page",
    ]
    assert reply.actions[-1]["refs"]["page_id"] == Page.objects.get(shared=False).id

    # Submitting the generated form creates the row.
    form = FormContainerElement.objects.get()
    name_input, tier_input = Element.objects.filter(parent_element=form).order_by(
        "order"
    )
    create_row = BuilderWorkflowAction.objects.get(
        element=form, content_type__model="localjadawelcreaterowworkflowaction"
    )
    response = api_client.post(
        reverse(
            "api:builder:workflow_action:dispatch",
            kwargs={"workflow_action_id": create_row.id},
        ),
        {
            "metadata": json.dumps(
                {"form_data": {name_input.id: "Salem", tier_input.id: "Gold"}}
            )
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {ws['token']}",
    )
    assert response.status_code == HTTP_200_OK, response.json()
    row = table.get_model().objects.get(**{f"field_{fields['name'].id}": "Salem"})
    assert getattr(row, f"field_{fields['tier'].id}").value == "Gold"


@pytest.mark.django_db(transaction=True)
def test_a_form_links_rows_through_a_dropdown_of_the_linked_table(
    api_client, ws, data_fixture
):
    """A link-to-table field is asked for with a dropdown of the linked table's
    rows; it used to be skipped, so forms could not set a task's project."""

    table, fields = ws["table"], ws["fields"]
    projects = data_fixture.create_database_table(
        database=table.database, name="Projects"
    )
    title = data_fixture.create_text_field(table=projects, name="Title", primary=True)
    alpha, beta = (
        RowHandler()
        .create_rows(
            ws["user"],
            projects,
            [{f"field_{title.id}": "Alpha"}, {f"field_{title.id}": "Beta"}],
        )
        .created_rows
    )
    link = data_fixture.create_link_row_field(
        table=table, link_row_table=projects, name="Project"
    )
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    page = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="New",
        path="/",
    )
    # A table of the same name on the page must not clash with the dropdown's source.
    run(
        "add_table_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=projects.id,
    )

    result = run(
        "add_form_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=table.id,
        field_ids=[fields["name"].id, link.id],
    )

    assert [item["field"] for item in result["inputs"]] == ["Name", "Project"]
    assert result["skipped_fields"] == []
    choice = ChoiceElement.objects.get(id=result["inputs"][1]["id"])
    assert choice.option_type == ChoiceElement.OPTION_TYPE.FORMULAS
    assert choice.multiple is True
    source = DataSource.objects.get(page_id=page["page_id"], name="Project (Projects)")
    assert source.service.specific.table_id == projects.id
    assert source.service.specific.default_result_count == 200
    assert choice.formula_value["formula"] == f"get('data_source.{source.id}.*.id')"
    assert choice.formula_name["formula"] == (
        f"get('data_source.{source.id}.*.field_{title.id}')"
    )

    name_input = Element.objects.get(id=result["inputs"][0]["id"])
    create_row = BuilderWorkflowAction.objects.get(
        element_id=result["form_element_id"],
        content_type__model="localjadawelcreaterowworkflowaction",
    )

    def submit(name, project):
        return api_client.post(
            reverse(
                "api:builder:workflow_action:dispatch",
                kwargs={"workflow_action_id": create_row.id},
            ),
            {
                "metadata": json.dumps(
                    {"form_data": {name_input.id: name, choice.id: project}}
                )
            },
            format="json",
            HTTP_AUTHORIZATION=f"JWT {ws['token']}",
        )

    response = submit("Salem", [alpha.id, beta.id])
    assert response.status_code == HTTP_200_OK, response.json()
    row = table.get_model().objects.get(**{f"field_{fields['name'].id}": "Salem"})
    assert {r.id for r in getattr(row, f"field_{link.id}").all()} == {
        alpha.id,
        beta.id,
    }

    # Only the linked table's rows are options.
    assert submit("Nora", [999999]).status_code != HTTP_200_OK
    assert (
        not table.get_model()
        .objects.filter(**{f"field_{fields['name'].id}": "Nora"})
        .exists()
    )


@pytest.mark.django_db(transaction=True)
def test_a_single_link_dropdown_submits_one_row(api_client, ws, data_fixture):
    table, fields = ws["table"], ws["fields"]
    team = data_fixture.create_database_table(database=table.database, name="Team")
    member = data_fixture.create_text_field(table=team, name="Member", primary=True)
    [noura] = (
        RowHandler()
        .create_rows(ws["user"], team, [{f"field_{member.id}": "Noura"}])
        .created_rows
    )
    assignee = data_fixture.create_link_row_field(
        table=table,
        link_row_table=team,
        name="Assignee",
        link_row_multiple_relationships=False,
    )
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    page = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="New",
        path="/",
    )
    result = run(
        "add_form_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=table.id,
        field_ids=[fields["name"].id, assignee.id],
    )
    name_input, choice = (item["id"] for item in result["inputs"])
    assert ChoiceElement.objects.get(id=choice).multiple is False
    create_row = BuilderWorkflowAction.objects.get(
        element_id=result["form_element_id"],
        content_type__model="localjadawelcreaterowworkflowaction",
    )

    response = api_client.post(
        reverse(
            "api:builder:workflow_action:dispatch",
            kwargs={"workflow_action_id": create_row.id},
        ),
        {"metadata": json.dumps({"form_data": {name_input: "Task", choice: noura.id}})},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {ws['token']}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    row = table.get_model().objects.get(**{f"field_{fields['name'].id}": "Task"})
    assert [r.id for r in getattr(row, f"field_{assignee.id}").all()] == [noura.id]


@pytest.mark.django_db(transaction=True)
def test_fields_are_added_to_an_existing_form(api_client, ws, data_fixture):
    table, fields = ws["table"], ws["fields"]
    projects = data_fixture.create_database_table(
        database=table.database, name="Projects"
    )
    title = data_fixture.create_text_field(table=projects, name="Title", primary=True)
    [alpha] = (
        RowHandler()
        .create_rows(ws["user"], projects, [{f"field_{title.id}": "Alpha"}])
        .created_rows
    )
    link = data_fixture.create_link_row_field(
        table=table, link_row_table=projects, name="Project"
    )
    app = run("create_builder_application", ws["endpoint"], name="Portal")
    page = run(
        "create_page",
        ws["endpoint"],
        application_id=app["application_id"],
        name="New",
        path="/",
    )
    form = run(
        "add_form_to_page",
        ws["endpoint"],
        page_id=page["page_id"],
        table_id=table.id,
        field_ids=[fields["name"].id],
    )

    added = run(
        "add_fields_to_form",
        ws["endpoint"],
        form_element_id=form["form_element_id"],
        field_ids=[fields["name"].id, link.id],
    )

    # The name is already asked for; only the project is added.
    assert [item["field"] for item in added["inputs"]] == ["Project"]
    children = Element.objects.filter(parent_element_id=form["form_element_id"])
    assert [child.get_type().type for child in children.order_by("order")] == [
        "input_text",
        "choice",
    ]
    create_row = BuilderWorkflowAction.objects.get(
        element_id=form["form_element_id"],
        content_type__model="localjadawelcreaterowworkflowaction",
    )
    response = api_client.post(
        reverse(
            "api:builder:workflow_action:dispatch",
            kwargs={"workflow_action_id": create_row.id},
        ),
        {
            "metadata": json.dumps(
                {
                    "form_data": {
                        form["inputs"][0]["id"]: "Salem",
                        added["inputs"][0]["id"]: [alpha.id],
                    }
                }
            )
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {ws['token']}",
    )
    assert response.status_code == HTTP_200_OK, response.json()
    row = table.get_model().objects.get(**{f"field_{fields['name'].id}": "Salem"})
    assert [r.id for r in getattr(row, f"field_{link.id}").all()] == [alpha.id]

    with pytest.raises(ValueError):
        run(
            "add_fields_to_form",
            ws["endpoint"],
            form_element_id=form["form_element_id"],
            field_ids=[link.id],
        )


@pytest.mark.django_db
def test_add_fields_to_form_stays_in_the_chat_workspace(ws, data_fixture):
    other_user = data_fixture.create_user(is_staff=True)
    other_workspace = data_fixture.create_workspace(user=other_user)
    other = SanadEndpoint(user=other_user, workspace=other_workspace)
    database = data_fixture.create_database_application(workspace=other_workspace)
    table = data_fixture.create_database_table(database=database, name="Theirs")
    name = data_fixture.create_text_field(table=table, name="Name", primary=True)
    note = data_fixture.create_text_field(table=table, name="Note")
    app = run("create_builder_application", other, name="Theirs")
    page = run(
        "create_page", other, application_id=app["application_id"], name="P", path="/"
    )
    form = run(
        "add_form_to_page",
        other,
        page_id=page["page_id"],
        table_id=table.id,
        field_ids=[name.id],
    )
    data_fixture.create_user_workspace(workspace=other_workspace, user=ws["user"])

    with pytest.raises(Exception):
        run(
            "add_fields_to_form",
            ws["endpoint"],
            form_element_id=form["form_element_id"],
            field_ids=[note.id],
        )
    assert (
        Element.objects.filter(parent_element_id=form["form_element_id"]).count() == 1
    )
