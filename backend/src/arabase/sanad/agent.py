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

from django.db import transaction

from arabase.sanad.exceptions import (
    SanadModelNotAvailable,
    SanadNoModelAvailable,
    SanadTurnTooLong,
)
from arabase.sanad.skills import loaded_skills, skills_index
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
databases, tables, fields, views, rows, automations, applications, \
dashboards and pages in their current workspace by calling tools. Everything \
you do runs with the user's own permissions.

How to work:
- Reply in the language the user writes in. Arabic is the default; keep \
Western digits (0-9), field names and technical tokens as they are.
- Never guess IDs. Discover them with list_databases, list_tables and \
get_table_schema before you create, change or delete anything.
- Prefer doing over explaining: when the request is clear, call the tools, \
then briefly say what you changed. When several calls do not depend on each \
other, make them in the same response, and give each call every argument it \
needs at once rather than fixing things one setting at a time. Ask one \
short question only when the request is genuinely ambiguous.
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
- Forms can set every writable field: a link-to-table field (a task's \
project or assignee) becomes a dropdown of the linked table's rows. To ask \
for more fields in a form that exists, use add_fields_to_form; do not build \
a second form.
- Tell the user the app is ready to preview in the editor; publishing it to a \
domain is done by the user in the app's settings.

Pages (صفحة): a Page view is a table view that shows an HTML page written \
for the table's rows. When the user gives a page number ("page 91", \
"الصفحة رقم 91") or asks for an HTML page on their data, that number is the \
Page view's ID: load the html-pages skill. It is not an application page.

- Keep answers short, clear and well structured. Use Markdown lists for steps.
"""

MAX_MODEL_REQUESTS = 40
"""Upper bound on model round-trips for one turn, so a confused model that
keeps calling tools cannot run up an unbounded provider bill. Building a
dashboard or a multi-page app well takes 15-25 tool calls on models that make
one call per request, so the bound leaves room for that and no more."""

TURN_TIME_LIMIT = 540
"""Seconds. A turn runs in a thread (``runner``), which nothing can kill, so it
checks this itself before each tool call. A call arriving later is refused and
its work lost, so the limit leaves room for the longest single output: writing
a Page view's document took one model request about four minutes through
OpenRouter."""

MODEL_REQUEST_TIMEOUT = 120
"""Seconds a model request may stay silent. The HTTP client applies it to each
read rather than to the whole request, so a provider that streams keep-alive
bytes (OpenRouter does) can take longer; ``TURN_TIME_LIMIT`` and
``handler.STALE_AFTER`` bound the turn as a whole."""


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
        "dashboard_id",
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
            # One transaction per call, as each editor API request has: tools
            # that lock rows need one, and a failed call leaves nothing half
            # done. Turns run on a thread with no request around them.
            with transaction.atomic():
                result = tool.call(ctx.deps.endpoint, arguments)
        except Exception as exc:  # noqa: BLE001 - reported back to the model
            logger.info("Sanad tool %s failed: %s", tool.name, exc.__class__.__name__)
            action.update(ok=False, error=safe_tool_error(exc))
            ctx.deps.on_action(action)
            return {"error": action["error"]}
        action["refs"] = _result_refs(result)
        ctx.deps.on_action(action)
        return result

    pydantic_ai_tool = Tool.from_schema(
        run,
        name=tool.name,
        description=tool.description,
        json_schema=tool.json_schema(),
        takes_ctx=True,
        # Tools mutate the same workspace; running them one at a time keeps
        # their effects in the order the model asked for.
        sequential=True,
    )
    if tool.skill:
        # Hidden until its skill is loaded, so the model builds with the
        # skill's guidance rather than guessing at a specialist tool.
        pydantic_ai_tool.prepare = lambda ctx, definition: (
            definition if tool.skill in loaded_skills(ctx.messages) else None
        )
    return pydantic_ai_tool


def build_instructions() -> str:
    return f"""{SANAD_INSTRUCTIONS}
Skills:
Each skill is expert guidance for one kind of work. When you are about to do \
that work — build it, change it, or answer how to — call load_skill with its \
name first, once per conversation: its instructions then stay in this \
conversation, so never load the same skill twice. Do not load skills for \
anything else. Some tools only appear after their skill is loaded.
{skills_index()}
"""


def build_agent(model):
    from pydantic_ai import Agent, DeferredToolRequests

    return Agent(
        model,
        instructions=build_instructions(),
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
    usage=None,
    token_budget: Optional[int] = None,
) -> TurnResult:
    """Run the model until it answers or pauses for an approval.

    Pass ``user_prompt`` for a new message, or ``decisions`` (tool call ID →
    approved) to resume a turn that paused for the user's approval.

    ``usage`` (a pydantic-ai ``RunUsage``) is filled in as the run goes, so the
    caller can bill what a failed run used too. ``token_budget`` caps the run's
    tokens at what is left of the workspace's month (``budget``).
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
        "usage_limits": UsageLimits(
            request_limit=MAX_MODEL_REQUESTS, total_tokens_limit=token_budget
        ),
        "usage": usage,
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
