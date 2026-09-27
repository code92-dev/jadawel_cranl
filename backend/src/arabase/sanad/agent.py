"""Runs one Sanad turn: the model, its tools, and the approval pause.

The model comes from core's generative AI registry, so Sanad uses whichever
providers the instance already configures through ``JADAWEL_OPENAI_API_KEY``,
``JADAWEL_ANTHROPIC_API_KEY``, ``JADAWEL_OLLAMA_HOST`` and friends — there is
no Sanad-specific credential. Each provider returns a pydantic-ai model, and
pydantic-ai drives the tool-calling loop.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from arabase.sanad.exceptions import (
    SanadModelNotAvailable,
    SanadNoModelAvailable,
    SanadTurnTooLong,
)
from arabase.sanad.tools import (
    SanadEndpoint,
    SanadTool,
    get_sanad_tools,
    safe_tool_error,
)
from jadawel.core.models import Workspace

logger = logging.getLogger(__name__)

SANAD_INSTRUCTIONS = """\
You are Sanad (سند), the AI assistant built into Jadawel (جداول), an \
Arabic-first spreadsheet-database. You help the user build and work with \
databases, tables, fields, views and rows in their current workspace by \
calling tools. Everything you do runs with the user's own permissions.

How to work:
- Reply in the language the user writes in. Arabic is the default; keep \
Western digits (0-9), field names and technical tokens as they are.
- Never guess IDs. Discover them with list_databases, list_tables and \
get_table_schema before you create, change or delete anything.
- Prefer doing over explaining: when the request is clear, call the tools, \
then briefly say what you changed. Ask one short question only when the \
request is genuinely ambiguous.
- Deleting a table, field, view or rows pauses for the user's approval in \
the chat. Call the delete tool directly; the user sees an approve/decline \
prompt. If they decline, accept it and do not retry.
- When the user describes a calculation, create or update a formula field. \
Jadawel formulas use the Baserow formula language: reference fields with \
field('Field name'), e.g. field('Price') * field('Quantity'), \
if(field('Stock') < 5, 'Low', 'OK'), concat(field('First'), ' ', \
field('Last')), datetime_format(field('Date'), 'YYYY-MM-DD'), \
date_diff('dd', field('Start'), field('End')), totext(), tonumber(), \
lookup('Link field', 'Field in linked table'), sum(lookup(...)). Pass the \
formula in the field spec as {"type": "formula", "formula": "..."}.
- Field specs accept the field type's own options, e.g. single_select \
{"select_options": [{"value": "Open", "color": "blue"}]}, number \
{"number_decimal_places": 2}, link_row {"link_row_table_id": 12}, \
date {"date_include_time": false}.
- Summarise data by reading rows with list_table_rows; do not invent values.

Automations (workflows that run by themselves):
- create_automation returns a first workflow; add its trigger with \
add_automation_step (no after_step_id), then each action after the previous \
step. Call describe_automation_step for a step's settings before using it, \
and get_table_schema for field IDs.
- Settings text is a formula: quote literal text ('Hello') and read earlier \
steps with get('previous_node.<step id>.0.field_<field id>') after a row \
trigger. Check the result with get_workflow.
- Map values to the right fields: each mapping you get back names its \
field. A single select takes an existing option's exact text, a link field \
takes row IDs.
- Publishing makes a workflow act on real data; call publish_workflow only \
when the user asked for it or agreed, and it pauses for their approval.
- Only the published version runs, a few seconds after its trigger. To check \
an automation, call get_workflow_runs and read each run's status and error; \
a missing result right after the trigger usually means the run has not \
finished yet, not that the trigger failed.

Application builder (web pages and portals):
- create_builder_application, then create_page (the home page's path is /), \
then add_page_content for headings, text, links and images (plain text, not \
formulas), add_table_to_page to list a table's rows, add_form_to_page for a \
form that adds rows. Link pages to each other with to_page_id.
- Tell the user the app is ready to preview in the editor; publishing it to a \
domain is done by the user in the app's settings.

- Keep answers short, clear and well structured. Use Markdown lists for steps.
"""

MAX_MODEL_REQUESTS = 25
"""Upper bound on model round-trips for one turn, so a confused model that
keeps calling tools cannot run up an unbounded provider bill."""

TURN_TIME_LIMIT = 300
"""Seconds. A turn runs in a thread (``runner``), which nothing can kill, so it
checks this itself before each tool call."""

MODEL_REQUEST_TIMEOUT = 120
"""Seconds one model request may take, so a hung provider cannot hold a turn
past ``handler.STALE_AFTER``."""


def get_available_models(workspace: Optional[Workspace] = None) -> list[str]:
    """Every enabled model as ``<provider type>/<model name>``."""

    from jadawel.core.generative_ai.registries import (
        generative_ai_model_type_registry,
    )

    models = []
    for (
        provider,
        names,
    ) in generative_ai_model_type_registry.get_enabled_models_per_type(
        workspace
    ).items():
        models += [f"{provider}/{name}" for name in names]
    return models


def resolve_model_choice(requested: str, workspace: Optional[Workspace] = None) -> str:
    """Return ``requested`` if enabled, else the first enabled model.

    :raises SanadNoModelAvailable: when no provider is configured at all.
    :raises SanadModelNotAvailable: when ``requested`` is not enabled.
    """

    available = get_available_models(workspace)
    if not available:
        raise SanadNoModelAvailable()
    if requested:
        if requested not in available:
            raise SanadModelNotAvailable()
        return requested
    return available[0]


def build_ai_model(model_choice: str, workspace: Optional[Workspace] = None):
    from jadawel.core.generative_ai.registries import (
        generative_ai_model_type_registry,
    )

    provider, _, model_name = model_choice.partition("/")
    return generative_ai_model_type_registry.get(provider).get_ai_model(
        model_name, workspace=workspace
    )


@dataclass
class SanadDeps:
    endpoint: SanadEndpoint
    on_action: Callable[[dict], None]
    actions: list = field(default_factory=list)
    deadline: float = field(default_factory=lambda: time.monotonic() + TURN_TIME_LIMIT)


def _result_refs(result: Any) -> dict:
    """IDs worth linking to from the chat, pulled out of a tool result."""

    if not isinstance(result, dict):
        return {}
    refs = {}
    for key in (
        "id",
        "table_id",
        "database_id",
        "view_id",
        "automation_id",
        "workflow_id",
        "application_id",
        "page_id",
    ):
        if isinstance(result.get(key), int):
            refs[key] = result[key]
    return refs


def _to_pydantic_ai_tool(tool: SanadTool):
    from pydantic_ai import ApprovalRequired, RunContext, Tool

    def run(ctx: RunContext[SanadDeps], **arguments):
        if time.monotonic() > ctx.deps.deadline:
            raise SanadTurnTooLong()
        if tool.needs_approval and not ctx.tool_call_approved:
            raise ApprovalRequired()
        action = {"tool": tool.name, "arguments": arguments, "ok": True}
        try:
            result = tool.call(ctx.deps.endpoint, arguments)
        except Exception as exc:  # noqa: BLE001 - reported back to the model
            logger.info("Sanad tool %s failed: %s", tool.name, exc.__class__.__name__)
            action.update(ok=False, error=safe_tool_error(exc))
            ctx.deps.on_action(action)
            return {"error": action["error"]}
        action["refs"] = _result_refs(result)
        ctx.deps.on_action(action)
        return result

    return Tool.from_schema(
        run,
        name=tool.name,
        description=tool.description,
        json_schema=tool.json_schema(),
        takes_ctx=True,
        # Tools mutate the same workspace; running them one at a time keeps
        # their effects in the order the model asked for.
        sequential=True,
    )


def build_agent(model):
    from pydantic_ai import Agent, DeferredToolRequests

    return Agent(
        model,
        instructions=SANAD_INSTRUCTIONS,
        deps_type=SanadDeps,
        tools=[_to_pydantic_ai_tool(tool) for tool in get_sanad_tools()],
        output_type=[str, DeferredToolRequests],
        model_settings={"timeout": MODEL_REQUEST_TIMEOUT},
    )


def load_history(history: list) -> list:
    from pydantic_ai.messages import ModelMessagesTypeAdapter

    return ModelMessagesTypeAdapter.validate_python(history) if history else []


def dump_history(messages: list) -> list:
    from pydantic_ai.messages import ModelMessagesTypeAdapter

    return ModelMessagesTypeAdapter.dump_python(messages, mode="json")


def build_user_prompt(content: str, context: dict) -> str:
    """Prefix the user's text with what they are looking at in the app."""

    hints = []
    if context.get("table_id"):
        hints.append(f"table_id={context['table_id']}")
    if context.get("view_id"):
        hints.append(f"view_id={context['view_id']}")
    if not hints:
        return content
    return f"[The user currently has open: {', '.join(hints)}]\n\n{content}"


@dataclass
class TurnResult:
    text: str
    approvals: list
    history: list


def run_turn(
    *,
    model,
    endpoint: SanadEndpoint,
    history: list,
    on_action: Callable[[dict], None],
    user_prompt: Optional[str] = None,
    decisions: Optional[dict[str, bool]] = None,
) -> TurnResult:
    """Run the model until it answers or pauses for an approval.

    Pass ``user_prompt`` for a new message, or ``decisions`` (tool call ID →
    approved) to resume a turn that paused for the user's approval.
    """

    from pydantic_ai import (
        DeferredToolRequests,
        DeferredToolResults,
        ToolDenied,
        UsageLimits,
    )

    agent = build_agent(model)
    deps = SanadDeps(endpoint=endpoint, on_action=on_action)
    kwargs = {
        "message_history": load_history(history),
        "deps": deps,
        "usage_limits": UsageLimits(request_limit=MAX_MODEL_REQUESTS),
    }
    if decisions is not None:
        kwargs["deferred_tool_results"] = DeferredToolResults(
            approvals={
                call_id: True
                if approved
                else ToolDenied("The user declined this action. Do not retry it.")
                for call_id, approved in decisions.items()
            }
        )
        result = agent.run_sync(**kwargs)
    else:
        result = agent.run_sync(user_prompt, **kwargs)

    history = dump_history(result.all_messages())
    if isinstance(result.output, DeferredToolRequests):
        approvals = [
            {
                "tool_call_id": call.tool_call_id,
                "tool": call.tool_name,
                "arguments": call.args_as_dict(),
            }
            for call in result.output.approvals
        ]
        return TurnResult(
            text=_text_before_pause(result), approvals=approvals, history=history
        )
    return TurnResult(text=str(result.output), approvals=[], history=history)


def _text_before_pause(result) -> str:
    """Whatever the model said alongside the calls it wants approved."""

    from pydantic_ai.messages import ModelResponse, TextPart

    for message in reversed(result.new_messages()):
        if isinstance(message, ModelResponse):
            return "\n".join(
                part.content for part in message.parts if isinstance(part, TextPart)
            ).strip()
    return ""
