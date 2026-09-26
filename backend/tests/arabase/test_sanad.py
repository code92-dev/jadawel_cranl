"""Sanad (سند), the in-app AI assistant — docs/SANAD_AI_ASSISTANT.md.

The model is replaced by a scripted pydantic-ai ``FunctionModel``: each test
lists the tool calls the "model" makes and asserts what really happened in the
workspace, so the tool wiring, permissions and approval pause are exercised
end to end without a provider.
"""

from datetime import timedelta
from unittest.mock import patch

from django.shortcuts import reverse
from django.utils import timezone

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from arabase.sanad.models import SanadChat, SanadMessage, SanadMessageStatus
from arabase.sanad.tools import APPROVAL_TOOLS, get_sanad_tools
from jadawel.contrib.database.table.models import Table
from jadawel.contrib.database.views.models import View, ViewFilter, ViewSort

MODEL = "openai/test-model"


def scripted_model(steps):
    """A model that plays ``steps`` in order, one per model request.

    A step is either a string (the final answer) or a list of
    ``(tool name, arguments)`` calls made in one response.
    """

    remaining = list(steps)
    seen_tool_results = []

    def respond(messages, info):
        for part in messages[-1].parts:
            if part.part_kind in ("tool-return", "retry-prompt"):
                seen_tool_results.append(part.content)
        step = remaining.pop(0)
        if isinstance(step, str):
            return ModelResponse(parts=[TextPart(step)])
        return ModelResponse(
            parts=[
                ToolCallPart(name, args, tool_call_id=f"call-{name}-{index}")
                for index, (name, args) in enumerate(step)
            ]
        )

    model = FunctionModel(respond)
    model.seen_tool_results = seen_tool_results
    return model


@pytest.fixture
def sanad(data_fixture):
    """A staff member with a workspace, a database and a table."""

    user, token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace, name="CRM")
    table = data_fixture.create_database_table(database=database, name="Customers")
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    return {
        "user": user,
        "token": token,
        "workspace": workspace,
        "database": database,
        "table": table,
        "name_field": name_field,
    }


def auth(token):
    return {"HTTP_AUTHORIZATION": f"JWT {token}"}


def chats_url(workspace):
    return reverse("api:arabase:sanad_chats", kwargs={"workspace_id": workspace.id})


def send(api_client, token, chat_id, content, model_script, **extra):
    with (
        patch(
            "arabase.sanad.agent.get_available_models",
            return_value=[MODEL],
        ),
        patch("arabase.sanad.agent.build_ai_model", return_value=model_script),
    ):
        return api_client.post(
            reverse("api:arabase:sanad_messages", kwargs={"chat_id": chat_id}),
            {"content": content, **extra},
            format="json",
            **auth(token),
        )


def decide(api_client, token, chat_id, decisions, model_script):
    with patch("arabase.sanad.agent.build_ai_model", return_value=model_script):
        return api_client.post(
            reverse("api:arabase:sanad_decisions", kwargs={"chat_id": chat_id}),
            {
                "decisions": [
                    {"tool_call_id": call_id, "approved": approved}
                    for call_id, approved in decisions.items()
                ]
            },
            format="json",
            **auth(token),
        )


def new_chat(api_client, sanad):
    response = api_client.post(chats_url(sanad["workspace"]), **auth(sanad["token"]))
    assert response.status_code == HTTP_200_OK, response.json()
    return response.json()["id"]


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_non_staff_members_cannot_use_sanad(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=False)
    workspace = data_fixture.create_workspace(user=user)

    for url in (
        chats_url(workspace),
        reverse("api:arabase:sanad_models", kwargs={"workspace_id": workspace.id}),
    ):
        response = api_client.get(url, **auth(token))
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json()["error"] == "ERROR_SANAD_NOT_ALLOWED"

    response = api_client.post(chats_url(workspace), **auth(token))
    assert response.status_code == HTTP_403_FORBIDDEN
    assert not SanadChat.objects.exists()


@pytest.mark.django_db
def test_anonymous_requests_are_rejected(api_client, sanad):
    response = api_client.get(chats_url(sanad["workspace"]))
    assert response.status_code == 401


@pytest.mark.django_db
def test_staff_outside_the_workspace_cannot_use_it(api_client, data_fixture, sanad):
    _, outsider_token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.post(chats_url(sanad["workspace"]), **auth(outsider_token))

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_a_chat_is_private_to_its_author(api_client, data_fixture, sanad):
    chat_id = new_chat(api_client, sanad)
    colleague, colleague_token = data_fixture.create_user_and_token(is_staff=True)
    data_fixture.create_user_workspace(workspace=sanad["workspace"], user=colleague)

    url = reverse("api:arabase:sanad_chat", kwargs={"chat_id": chat_id})
    assert api_client.get(url, **auth(colleague_token)).status_code == (
        HTTP_404_NOT_FOUND
    )
    listed = api_client.get(chats_url(sanad["workspace"]), **auth(colleague_token))
    assert listed.json() == []
    assert api_client.delete(url, **auth(colleague_token)).status_code == (
        HTTP_404_NOT_FOUND
    )
    assert api_client.delete(url, **auth(sanad["token"])).status_code == (
        HTTP_204_NO_CONTENT
    )


@pytest.mark.django_db
def test_sending_without_a_configured_provider_fails_clearly(api_client, sanad):
    chat_id = new_chat(api_client, sanad)

    with patch("arabase.sanad.agent.get_available_models", return_value=[]):
        response = api_client.post(
            reverse("api:arabase:sanad_messages", kwargs={"chat_id": chat_id}),
            {"content": "hello"},
            format="json",
            **auth(sanad["token"]),
        )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_SANAD_NO_MODEL_AVAILABLE"
    assert not SanadMessage.objects.exists()


@pytest.mark.django_db
def test_an_unknown_model_is_rejected(api_client, sanad):
    chat_id = new_chat(api_client, sanad)

    response = send(
        api_client, sanad["token"], chat_id, "hi", scripted_model([]), model="x/y"
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_SANAD_MODEL_NOT_AVAILABLE"


# ---------------------------------------------------------------------------
# Turns
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_a_turn_builds_a_table_with_a_formula_field(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [
            [("list_databases", {})],
            [
                (
                    "create_table",
                    {
                        "database_id": sanad["database"].id,
                        "name": "الطلبات",
                        "fields": [
                            {"name": "السعر", "type": "number"},
                            {"name": "الكمية", "type": "number"},
                            {
                                "name": "الإجمالي",
                                "type": "formula",
                                "formula": "field('السعر') * field('الكمية')",
                            },
                        ],
                    },
                )
            ],
            "أنشأت جدول الطلبات مع حقل الإجمالي.",
        ]
    )

    response = send(
        api_client,
        sanad["token"],
        chat_id,
        "أنشئ جدول طلبات فيه السعر والكمية والإجمالي",
        model,
        context={"table_id": sanad["table"].id},
    )

    assert response.status_code == HTTP_202_ACCEPTED, response.json()
    table = Table.objects.get(name="الطلبات")
    assert table.database_id == sanad["database"].id
    formula = table.field_set.get(name="الإجمالي").specific
    assert formula.formula == "field('السعر') * field('الكمية')"

    chat = api_client.get(
        reverse("api:arabase:sanad_chat", kwargs={"chat_id": chat_id}),
        **auth(sanad["token"]),
    ).json()
    user_message, reply = chat["messages"]
    assert user_message["role"] == "user"
    assert user_message["context"] == {"table_id": sanad["table"].id}
    assert reply["status"] == SanadMessageStatus.DONE
    assert reply["content"] == "أنشأت جدول الطلبات مع حقل الإجمالي."
    assert [action["tool"] for action in reply["actions"]] == [
        "list_databases",
        "create_table",
    ]
    assert all(action["ok"] for action in reply["actions"])
    assert chat["title"] == "أنشئ جدول طلبات فيه السعر والكمية والإجمالي"
    assert chat["model"] == MODEL
    # The model saw the database listing, so it discovered the ID itself.
    assert sanad["database"].id in [db["id"] for db in model.seen_tool_results[0]]


@pytest.mark.django_db(transaction=True)
def test_the_open_table_is_passed_to_the_model(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    prompts = []

    def respond(messages, info):
        prompts.append(messages[-1].parts[-1].content)
        return ModelResponse(parts=[TextPart("ok")])

    send(
        api_client,
        sanad["token"],
        chat_id,
        "what is this?",
        FunctionModel(respond),
        context={"table_id": sanad["table"].id, "view_id": None},
    )

    assert prompts == [
        f"[The user currently has open: table_id={sanad['table'].id}]\n\nwhat is this?"
    ]


@pytest.mark.django_db(transaction=True)
def test_follow_up_turns_keep_the_conversation(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    seen = []

    def respond(messages, info):
        seen.append(len(messages))
        return ModelResponse(parts=[TextPart("ok")])

    send(api_client, sanad["token"], chat_id, "first", FunctionModel(respond))
    send(api_client, sanad["token"], chat_id, "second", FunctionModel(respond))

    # The second request carries the first question and answer too.
    assert seen == [1, 3]


@pytest.mark.django_db(transaction=True)
def test_view_tools_create_a_filtered_sorted_view(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    table, field = sanad["table"], sanad["name_field"]
    model = scripted_model(
        [
            [
                (
                    "create_view",
                    {"table_id": table.id, "name": "عملاء أ", "type": "grid"},
                )
            ],
            "view created",
        ]
    )
    send(api_client, sanad["token"], chat_id, "make a view", model)
    view = View.objects.get(name="عملاء أ")

    model = scripted_model(
        [
            [
                (
                    "add_view_filter",
                    {
                        "view_id": view.id,
                        "field_id": field.id,
                        "type": "contains",
                        "value": "أ",
                    },
                ),
                (
                    "add_view_sort",
                    {"view_id": view.id, "field_id": field.id, "order": "desc"},
                ),
                ("list_views", {"table_id": table.id}),
            ],
            "done",
        ]
    )
    send(api_client, sanad["token"], chat_id, "filter and sort it", model)

    view_filter = ViewFilter.objects.get(view=view)
    assert (view_filter.type, view_filter.value) == ("contains", "أ")
    assert ViewSort.objects.get(view=view).order == "DESC"
    listed = model.seen_tool_results[-1]
    assert {"id": view.id, "name": "عملاء أ", "type": "grid"}.items() <= listed[
        -1
    ].items()


@pytest.mark.django_db(transaction=True)
def test_a_kanban_view_uses_a_single_select_field(api_client, data_fixture, sanad):
    table = sanad["table"]
    status = data_fixture.create_single_select_field(table=table, name="Status")
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [
            [
                (
                    "create_view",
                    {
                        "table_id": table.id,
                        "name": "Board",
                        "type": "kanban",
                        "single_select_field_id": status.id,
                    },
                )
            ],
            "board ready",
        ]
    )

    send(api_client, sanad["token"], chat_id, "kanban please", model)

    board = View.objects.get(name="Board").specific
    assert board.single_select_field_id == status.id


@pytest.mark.django_db(transaction=True)
def test_tools_cannot_reach_another_workspace(api_client, data_fixture, sanad):
    other_user = data_fixture.create_user()
    other_table = data_fixture.create_database_table(user=other_user)
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [
            [
                (
                    "create_view",
                    {"table_id": other_table.id, "name": "sneaky", "type": "grid"},
                ),
                ("list_table_rows", {"table_id": other_table.id}),
            ],
            "could not",
        ]
    )

    send(api_client, sanad["token"], chat_id, "look elsewhere", model)

    assert not View.objects.filter(name="sneaky").exists()
    reply = SanadMessage.objects.get(role="assistant")
    assert [action["ok"] for action in reply.actions] == [False, False]
    assert all("error" in result for result in model.seen_tool_results)


@pytest.mark.django_db(transaction=True)
def test_invalid_tool_arguments_are_reported_to_the_model(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [
            [
                (
                    "create_view",
                    {"table_id": sanad["table"].id, "name": "x", "type": "calendar"},
                )
            ],
            "sorry",
        ]
    )

    send(api_client, sanad["token"], chat_id, "calendar view", model)

    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.DONE
    assert reply.actions[0]["ok"] is False
    assert "Unsupported view type" in reply.actions[0]["error"]


# ---------------------------------------------------------------------------
# Approval of deletes and publishing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_every_delete_tool_needs_approval():
    names = {tool.name for tool in get_sanad_tools()}
    assert {name for name in names if name.startswith("delete_")} <= APPROVAL_TOOLS


@pytest.mark.django_db(transaction=True)
def test_deleting_rows_waits_for_approval(api_client, data_fixture, sanad):
    table = sanad["table"]
    model_class = table.get_model()
    row = model_class.objects.create(**{f"field_{sanad['name_field'].id}": "Aziz"})
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [
            [("delete_rows", {"table_id": table.id, "row_ids": [row.id]})],
            "Deleted.",
        ]
    )

    send(api_client, sanad["token"], chat_id, "delete Aziz", model)

    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.AWAITING_APPROVAL
    assert reply.approvals == [
        {
            "tool_call_id": "call-delete_rows-0",
            "tool": "delete_rows",
            "arguments": {"table_id": table.id, "row_ids": [row.id]},
        }
    ]
    assert model_class.objects.filter(id=row.id).exists()

    # The chat is blocked until the user decides.
    busy = send(api_client, sanad["token"], chat_id, "anything else?", model)
    assert busy.status_code == HTTP_409_CONFLICT
    assert busy.json()["error"] == "ERROR_SANAD_CHAT_BUSY"

    response = decide(
        api_client, sanad["token"], chat_id, {"call-delete_rows-0": True}, model
    )

    assert response.status_code == HTTP_202_ACCEPTED, response.json()
    assert not model_class.objects.filter(id=row.id).exists()
    reply.refresh_from_db()
    assert reply.status == SanadMessageStatus.DONE
    assert reply.content == "Deleted."
    assert reply.approvals[0]["approved"] is True
    assert [action["tool"] for action in reply.actions] == ["delete_rows"]


@pytest.mark.django_db(transaction=True)
def test_a_declined_delete_never_runs(api_client, sanad):
    table = sanad["table"]
    chat_id = new_chat(api_client, sanad)
    model = scripted_model(
        [[("delete_table", {"table_id": table.id})], "Understood, kept it."]
    )
    send(api_client, sanad["token"], chat_id, "delete the table", model)

    decide(api_client, sanad["token"], chat_id, {"call-delete_table-0": False}, model)

    assert Table.objects.filter(id=table.id).exists()
    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.DONE
    assert reply.actions == []
    assert "declined" in str(model.seen_tool_results[-1])


@pytest.mark.django_db(transaction=True)
def test_decisions_must_match_the_pending_calls(api_client, sanad):
    chat_id = new_chat(api_client, sanad)
    model = scripted_model([[("delete_table", {"table_id": sanad["table"].id})]])
    send(api_client, sanad["token"], chat_id, "delete it", model)

    response = decide(api_client, sanad["token"], chat_id, {"made-up": True}, model)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_SANAD_NOTHING_TO_APPROVE"
    assert Table.objects.filter(id=sanad["table"].id).exists()


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_a_model_failure_marks_the_turn_failed(api_client, sanad):
    chat_id = new_chat(api_client, sanad)

    def respond(messages, info):
        raise RuntimeError("provider is down, key sk-secret")

    send(api_client, sanad["token"], chat_id, "hi", FunctionModel(respond))

    reply = SanadMessage.objects.get(role="assistant")
    assert reply.status == SanadMessageStatus.ERROR
    assert reply.error == "SANAD_ERROR_MODEL_FAILED"
    assert "sk-secret" not in reply.content
    # The chat can be used again straight away.
    ok = send(
        api_client,
        sanad["token"],
        chat_id,
        "again",
        FunctionModel(lambda m, i: ModelResponse(parts=[TextPart("back")])),
    )
    assert ok.status_code == HTTP_202_ACCEPTED


@pytest.mark.django_db
def test_a_turn_whose_worker_died_is_released(api_client, sanad):
    chat = SanadChat.objects.create(user=sanad["user"], workspace=sanad["workspace"])
    stuck = SanadMessage.objects.create(
        chat=chat, role="assistant", status=SanadMessageStatus.PENDING
    )
    SanadMessage.objects.filter(id=stuck.id).update(
        updated_on=timezone.now() - timedelta(minutes=11)
    )

    response = api_client.get(
        reverse("api:arabase:sanad_chat", kwargs={"chat_id": chat.id}),
        **auth(sanad["token"]),
    )

    assert response.json()["messages"][0]["status"] == SanadMessageStatus.ERROR
    assert response.json()["messages"][0]["error"] == "SANAD_ERROR_TIMED_OUT"
