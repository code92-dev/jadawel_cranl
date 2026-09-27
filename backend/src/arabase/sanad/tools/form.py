"""Sanad's tools for Form views (نموذج): a table's rows, entered through a form.

``create_view`` alone makes an empty form: every field starts disabled, so the
form asks nothing until someone picks its fields. These tools build the form in
one call — its title, questions, order, labels, required flags, conditions and
what happens after submitting — and read it back, the way the form editor does.
They are offered once the ``forms`` skill is loaded.

Settings go through the view update serializer and ``UpdateViewActionType``,
questions through the view's field-options serializer and
``UpdateViewFieldOptionsActionType``: what the editor's own API would reject is
rejected here with the same message, and every change can be undone.
"""

from typing import Literal, Optional

from django.conf import settings

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import SanadEndpoint, SanadTool, select_option_ids

SKILL = "forms"

CHOICE_STYLES = {
    "single_select": ("default", "radios"),
    "multiple_select": ("default", "checkboxes"),
    "multiple_collaborators": ("default", "checkboxes"),
}
"""The input styles the form editor offers per field type (``fieldTypes.js``);
every other field has only ``default``."""


class FormCondition(BaseModel):
    field_id: int = Field(..., description="An earlier question's field.")
    type: str = Field(
        ...,
        description="A filter type, e.g. equal, not_equal, contains, empty, "
        "not_empty, boolean, higher_than, single_select_equal.",
    )
    value: str = Field(
        "",
        description="Compared with the answer. Select conditions take the "
        "option's text.",
    )


class FormQuestion(BaseModel):
    field_id: int = Field(..., description="The field this question fills in.")
    label: Optional[str] = Field(
        None, description="The question as the form shows it; default the field name."
    )
    description: Optional[str] = Field(
        None, description="Help text under the question."
    )
    required: bool = False
    style: Optional[Literal["default", "radios", "checkboxes"]] = Field(
        None,
        description="radios for a single select, checkboxes for a multiple "
        "select; default is a dropdown.",
    )
    show_when: list[FormCondition] = Field(
        default_factory=list,
        description="Show this question only when these conditions match the "
        "answers to earlier questions.",
    )
    show_when_any: bool = Field(
        False, description="Show when any condition matches instead of all."
    )


class FormSettings(BaseModel):
    title: Optional[str] = Field(None, description="The heading of the form.")
    description: Optional[str] = Field(
        None, description="Text under the title. Plain text; line breaks are kept."
    )
    submit_text: Optional[str] = Field(None, description="The submit button's text.")
    success_message: Optional[str] = Field(
        None, description="Shown after submitting. Plain text; line breaks are kept."
    )
    redirect_url: Optional[str] = Field(
        None,
        description="Go to this URL after submitting instead of showing a message.",
    )


class CreateFormInput(FormSettings):
    table_id: int = Field(..., description="The table each submission adds a row to.")
    name: str = Field(..., description="The view name.")
    questions: Optional[list[FormQuestion]] = Field(
        None,
        description="The questions, in order. Omit to ask every field that can "
        "be filled in, in the table's order.",
    )


class GetFormInput(BaseModel):
    view_id: int = Field(..., description="The Form view.")


class UpdateFormInput(FormSettings):
    view_id: int = Field(..., description="The Form view.")
    questions: Optional[list[FormQuestion]] = Field(
        None,
        description="Replaces every question: the form asks exactly these, in "
        "this order. Omit to keep the questions. Read get_form first.",
    )


class ShareFormInput(BaseModel):
    view_id: int = Field(..., description="The Form view.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_form(endpoint: SanadEndpoint, view_id: int):
    """A Form view in the chat's workspace that the user can see."""

    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.handler import ViewHandler

    view = ViewHandler().get_view(view_id).specific
    services.get_table(endpoint.user, endpoint.workspace, view.table_id)
    if view.get_type().type != "form":
        raise ValueError(
            f"View {view_id} is a {view.get_type().type} view, not a form."
        )
    return view


def _table_fields(table) -> list:
    return [
        field.specific
        for field in table.field_set.order_by("order", "id").prefetch_related(
            "select_options"
        )
    ]


def _unsupported_reason(field) -> Optional[str]:
    """Why a field cannot be a question, or ``None`` when it can."""

    from jadawel.contrib.database.fields.registries import field_type_registry

    field_type = field_type_registry.get_by_model(field)
    if field.read_only or field_type.read_only:
        return "computed or read-only"
    if not field_type.can_be_in_form_view:
        return f"a {field_type.type} field cannot be filled in on a form"
    return None


def _settings_values(args: FormSettings) -> dict:
    values = {
        "title": args.title,
        "description": args.description,
        "submit_text": args.submit_text,
    }
    if args.redirect_url is not None:
        values["submit_action"] = "REDIRECT"
        values["submit_action_redirect_url"] = args.redirect_url
    elif args.success_message is not None:
        values["submit_action"] = "MESSAGE"
        values["submit_action_message"] = args.success_message
    return {key: value for key, value in values.items() if value is not None}


def _validated_settings(values: dict) -> dict:
    """Validated by the serializer ``PATCH /api/database/views/<id>/`` uses."""

    from jadawel.api.exceptions import RequestBodyValidationException
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.database.api.views.serializers import UpdateViewSerializer
    from jadawel.contrib.database.views.registries import view_type_registry

    if not values:
        return {}
    try:
        validated = validate_data_custom_fields(
            "form",
            view_type_registry,
            {"type": "form", **values},
            base_serializer_class=UpdateViewSerializer,
            partial=True,
            return_validated=True,
        )
    except RequestBodyValidationException as exc:
        raise ValueError(f"Invalid form settings: {exc.detail['detail']}") from exc
    validated.pop("type", None)
    return validated


def _condition(fields_by_id: dict, question_ids: list, condition: FormCondition):
    from jadawel.contrib.database.views.registries import view_filter_type_registry

    field = fields_by_id.get(condition.field_id)
    if field is None:
        raise ValueError(f"Field {condition.field_id} is not in this table.")
    if condition.field_id not in question_ids:
        raise ValueError(
            f"A condition can only look at an earlier question; {field.name!r} "
            "is not asked before it."
        )
    filter_type = view_filter_type_registry.get(condition.type)
    if not filter_type.field_is_compatible(field):
        raise ValueError(
            f"The condition {condition.type!r} does not apply to {field.name!r}."
        )
    return {
        "field": field.id,
        "type": condition.type,
        "value": select_option_ids(field, condition.type, condition.value),
    }


def _question_options(view, questions: list[FormQuestion]) -> tuple[dict, list]:
    """Field options that make the form ask exactly ``questions``, in order."""

    from jadawel.contrib.database.fields.registries import field_type_registry

    fields = _table_fields(view.table)
    fields_by_id = {field.id: field for field in fields}
    seen = set()
    options = {}
    for index, question in enumerate(questions):
        field = fields_by_id.get(question.field_id)
        if field is None:
            raise ValueError(f"Field {question.field_id} is not in this table.")
        if question.field_id in seen:
            raise ValueError(f"{field.name!r} is asked twice.")
        reason = _unsupported_reason(field)
        if reason:
            raise ValueError(f"{field.name!r} cannot be a question: {reason}.")
        field_type = field_type_registry.get_by_model(field).type
        style = question.style or "default"
        if style not in CHOICE_STYLES.get(field_type, ("default",)):
            raise ValueError(
                f"{field.name!r} is a {field_type} field; it has no {style!r} style."
            )
        conditions = [
            {
                "id": -(index * 100 + position + 1),
                **_condition(fields_by_id, [*seen], c),
            }
            for position, c in enumerate(question.show_when)
        ]
        options[field.id] = {
            "enabled": True,
            "order": index,
            "name": question.label or "",
            "description": question.description or "",
            "required": question.required,
            "field_component": style,
            "show_when_matching_conditions": bool(conditions),
            "condition_type": "OR" if question.show_when_any else "AND",
            "conditions": conditions,
            "condition_groups": [],
        }
        seen.add(question.field_id)

    unasked = [field for field in fields if field.id not in options]
    for position, field in enumerate(unasked, start=len(questions)):
        options[field.id] = {
            "enabled": False,
            "order": position,
            "conditions": [],
            "condition_groups": [],
        }
    skipped = [
        {"field_id": field.id, "name": field.name, "reason": reason}
        for field in fields
        if (reason := _unsupported_reason(field))
    ]
    return options, skipped


def _apply_questions(endpoint: SanadEndpoint, view, questions) -> list:
    from jadawel.api.utils import validate_data
    from jadawel.contrib.database.views.actions import (
        UpdateViewFieldOptionsActionType,
    )

    options, skipped = _question_options(view, questions)
    serializer_class = view.get_type().get_field_options_serializer_class()
    data = validate_data(
        serializer_class,
        {"field_options": {str(key): value for key, value in options.items()}},
        return_validated=True,
    )
    UpdateViewFieldOptionsActionType.do(endpoint.user, view, field_options=data)
    return skipped


def _every_question(table) -> list[FormQuestion]:
    return [
        FormQuestion(field_id=field.id)
        for field in _table_fields(table)
        if not _unsupported_reason(field)
    ]


def _public_url(view) -> str:
    return f"{settings.PUBLIC_WEB_FRONTEND_URL}/form/{view.slug}"


def _describe_form(view) -> dict:
    from jadawel.contrib.database.fields.registries import field_type_registry

    view.refresh_from_db()
    fields = _table_fields(view.table)
    field_names = {field.id: field.name for field in fields}
    options = {
        option.field_id: option
        for option in view.get_field_options(create_if_missing=True).prefetch_related(
            "conditions"
        )
    }
    questions, not_asked = [], []
    for field in fields:
        option = options.get(field.id)
        field_type = field_type_registry.get_by_model(field).type
        if option is None or not option.enabled:
            not_asked.append(
                {
                    "field_id": field.id,
                    "name": field.name,
                    "type": field_type,
                    "cannot_be_asked": _unsupported_reason(field),
                }
            )
            continue
        questions.append(
            {
                "order": option.order,
                "field_id": field.id,
                "field_name": field.name,
                "type": field_type,
                "label": option.name or field.name,
                "description": option.description,
                "required": option.required,
                "style": option.field_component,
                "show_when": [
                    {
                        "field_id": condition.field_id,
                        "field_name": field_names.get(condition.field_id),
                        "type": condition.type,
                        "value": condition.value,
                    }
                    for condition in option.conditions.all()
                ]
                if option.show_when_matching_conditions
                else [],
                "show_when_any": option.condition_type == "OR",
            }
        )
    questions.sort(key=lambda question: (question["order"], question["field_id"]))
    for question in questions:
        del question["order"]
    return {
        "view_id": view.id,
        "name": view.name,
        "table_id": view.table_id,
        "database_id": view.table.database_id,
        "title": view.title,
        "description": view.description,
        "submit_text": view.submit_text,
        "after_submit": (
            {"redirect_url": view.submit_action_redirect_url}
            if view.submit_action == "REDIRECT"
            else {"message": view.submit_action_message}
        ),
        "shared": view.public,
        "public_url": _public_url(view) if view.public else None,
        "questions": questions,
        "not_asked": not_asked,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def create_form(endpoint: SanadEndpoint, args: CreateFormInput) -> dict:
    from jadawel.contrib.database.mcp import services
    from jadawel.contrib.database.views.actions import CreateViewActionType

    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    values = _validated_settings(_settings_values(args))
    view = CreateViewActionType.do(
        endpoint.user, table, "form", name=args.name, **values
    ).specific
    questions = args.questions if args.questions is not None else _every_question(table)
    skipped = _apply_questions(endpoint, view, questions)
    return {
        **_describe_form(view),
        "skipped_fields": skipped if args.questions is None else [],
    }


def get_form(endpoint: SanadEndpoint, args: GetFormInput) -> dict:
    return _describe_form(_get_form(endpoint, args.view_id))


def update_form(endpoint: SanadEndpoint, args: UpdateFormInput) -> dict:
    from jadawel.contrib.database.views.actions import UpdateViewActionType

    view = _get_form(endpoint, args.view_id)
    values = _validated_settings(_settings_values(args))
    if values:
        view = UpdateViewActionType.do(endpoint.user, view, **values).specific
    if args.questions is not None:
        _apply_questions(endpoint, view, args.questions)
    return _describe_form(view)


def share_form(endpoint: SanadEndpoint, args: ShareFormInput) -> dict:
    from jadawel.contrib.database.views.actions import UpdateViewActionType

    view = _get_form(endpoint, args.view_id)
    if not view.public:
        view = UpdateViewActionType.do(endpoint.user, view, public=True).specific
    return {"view_id": view.id, "shared": True, "public_url": _public_url(view)}


def get_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "create_form",
            "Create a Form view whose submissions add rows to a table, with its "
            "title, questions, order, required answers, conditions and the "
            "message after submitting — all in one call.",
            CreateFormInput,
            create_form,
            skill=SKILL,
        ),
        SanadTool(
            "get_form",
            "Read a Form view: its settings, its questions in order, and the "
            "fields it does not ask.",
            GetFormInput,
            get_form,
            skill=SKILL,
        ),
        SanadTool(
            "update_form",
            "Change a Form view's settings, or replace its questions.",
            UpdateFormInput,
            update_form,
            skill=SKILL,
        ),
        SanadTool(
            "share_form",
            "Turn on the form's public link so anyone with it can submit. Needs "
            "the user's approval.",
            ShareFormInput,
            share_form,
            skill=SKILL,
        ),
    ]
