"""The contract every Sanad tool implements, and helpers the domains share.

A tool is a ``SanadTool``: a name, a description, a pydantic input schema and a
function run as the signed-in user in the chat's workspace. The tools live in
one module per domain next to this one (``database``, ``form``, ``automation``,
``builder``, ``builder_elements``, ``dashboard``, ``page``); the package's
``get_sanad_tools`` gathers them. Helpers more than one domain needs live here,
so domains do not import each other; ``builder_elements`` extends ``builder``
and is the one exception.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from django.contrib.auth.models import AbstractUser

from pydantic import BaseModel, ValidationError

from jadawel.core.models import Workspace

# Tools that delete something, put a workflow live so it acts on real data
# unattended, or open a public link to a table. The model must get the user's
# explicit approval in the panel before any of them runs.
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
        "share_form",
    }
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


def describe_doc(doc: str | None) -> str:
    """A docstring collapsed to one line, as a tool description."""

    return " ".join((doc or "").split())


def safe_tool_error(exc: Exception) -> str:
    """A short error the model can act on, without a traceback."""

    if isinstance(exc, ValidationError):
        return f"Invalid arguments: {exc.errors(include_url=False)}"
    name = exc.__class__.__name__
    message = str(exc).strip()
    if name.endswith("DoesNotExist"):
        return f"{name}: not found or not accessible."
    return f"{name}: {message[:300]}" if message else name


def formula_literal(text: str) -> str:
    """A formula that evaluates to exactly ``text``."""

    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def application_type(application) -> str:
    from jadawel.core.registries import application_type_registry

    return application_type_registry.get_by_model(application.specific_class).type


def get_application(endpoint: SanadEndpoint, application_id: int, expected: str):
    """An application of the chat's workspace the user may read.

    :raises ApplicationDoesNotExist: for another workspace's application.
    :raises ValueError: when it is not of the expected type.
    """

    from jadawel.core.exceptions import ApplicationDoesNotExist
    from jadawel.core.handler import CoreHandler
    from jadawel.core.operations import ReadApplicationOperationType

    application = CoreHandler().get_application(application_id)
    if application.workspace_id != endpoint.workspace.id:
        raise ApplicationDoesNotExist(f"Application {application_id} not found.")
    CoreHandler().check_permissions(
        endpoint.user,
        ReadApplicationOperationType.type,
        workspace=application.workspace,
        context=application,
    )
    kind = application_type(application)
    if kind != expected:
        raise ValueError(f"Application {application_id} is a {kind}, not a {expected}.")
    return application.specific


def describe_field(field) -> dict:
    from rest_framework import serializers

    from jadawel.core.formula.serializers import FormulaSerializerField

    info = {"help": str(field.help_text or "")}
    if isinstance(field, FormulaSerializerField):
        info["type"] = "formula"
    elif isinstance(field, serializers.ChoiceField):
        info["type"] = "choice"
        info["choices"] = list(field.choices)
    elif isinstance(field, (serializers.ListSerializer, serializers.ListField)):
        info["type"] = "list"
        child = field.child
        info["item"] = (
            describe_serializer(child)
            if isinstance(child, serializers.Serializer)
            else describe_field(child)
        )
    elif isinstance(field, serializers.BooleanField):
        info["type"] = "boolean"
    elif isinstance(field, serializers.IntegerField):
        info["type"] = "integer"
    elif isinstance(field, serializers.Serializer):
        info["type"] = "object"
        info["fields"] = describe_serializer(field)
    else:
        info["type"] = "string"
    return info


def describe_serializer(serializer) -> dict:
    return {
        name: describe_field(field)
        for name, field in serializer.fields.items()
        if not field.read_only and name != "type"
    }


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


def select_option_ids(field, filter_type: str, value: str) -> str:
    """A select filter's value as option IDs, the only form it matches.

    Used for view filters and for form conditions, which take the same types.
    Models naturally write the option's text ("Open"); stored as-is, that
    filter matches nothing and the view silently shows every row, which once
    led a model to tell the user that filters are ignored.
    """

    if filter_type not in SELECT_FILTER_TYPES or not value.strip():
        return value
    options = {
        option.value.strip().casefold(): str(option.id)
        for option in field.select_options.all()
    }
    valid_ids = set(options.values())
    ids = []
    for part in value.split(","):
        part = part.strip()
        if part in valid_ids:
            ids.append(part)
        elif part.casefold() in options:
            ids.append(options[part.casefold()])
        else:
            names = ", ".join(option.value for option in field.select_options.all())
            raise ValueError(f"{part!r} is not an option of this field: {names}.")
    return ",".join(ids)
