"""Sanad's application-builder tools, at the level of intent.

They are deliberately higher level than the element API. A page is assembled
from a few intents — content, a table of rows, a form that saves a row — and
each one creates the data source, elements and workflow actions it needs through
the permission-checked builder services, following
``BuilderApplicationTypeInitApplication``. ``builder_elements`` reaches every
element the editor offers once the ``app-builder`` skill is loaded.
"""

from typing import Literal, Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import (
    SanadEndpoint,
    SanadTool,
    formula_literal,
    get_application,
)

LOCAL_INTEGRATION_NAME = "جداول المحلي"
"""What core names the integration it creates for a new app; matching it keeps
Sanad-built apps indistinguishable from hand-built ones."""


def local_integration(endpoint: SanadEndpoint, builder):
    """The builder's local data connection, created on first use."""

    from jadawel.core.integrations.registries import integration_type_registry
    from jadawel.core.integrations.service import IntegrationService

    service = IntegrationService()
    for integration in service.get_integrations(endpoint.user, builder):
        if integration.get_type().type == "local_jadawel":
            return integration
    return service.create_integration(
        endpoint.user,
        integration_type_registry.get("local_jadawel"),
        builder,
        name=LOCAL_INTEGRATION_NAME,
        authorized_user=endpoint.user,
    )


class CreateBuilderApplicationInput(BaseModel):
    name: str = Field(..., description="The application's name.")


def create_builder_application(
    endpoint: SanadEndpoint, args: CreateBuilderApplicationInput
) -> dict:
    from jadawel.core.actions import CreateApplicationActionType

    with transaction.atomic():
        # No demo content: Sanad builds the pages the user asked for.
        builder = CreateApplicationActionType.do(
            endpoint.user, endpoint.workspace, "builder", name=args.name
        ).specific
        integration = local_integration(endpoint, builder)
    return {
        "application_id": builder.id,
        "name": builder.name,
        "integration_id": integration.id,
    }


def get_page(endpoint: SanadEndpoint, page_id: int):
    from jadawel.contrib.builder.pages.exceptions import PageDoesNotExist
    from jadawel.contrib.builder.pages.service import PageService

    page = PageService().get_page(endpoint.user, page_id)
    if page.builder.workspace_id != endpoint.workspace.id or page.shared:
        raise PageDoesNotExist()
    return page


class ListPagesInput(BaseModel):
    application_id: int = Field(..., description="The builder application.")


def list_pages(endpoint: SanadEndpoint, args: ListPagesInput) -> list[dict]:
    from jadawel.contrib.builder.elements.service import ElementService
    from jadawel.contrib.builder.operations import ListPagesBuilderOperationType
    from jadawel.contrib.builder.pages.handler import PageHandler
    from jadawel.core.handler import CoreHandler

    builder = get_application(endpoint, args.application_id, "builder")
    CoreHandler().check_permissions(
        endpoint.user,
        ListPagesBuilderOperationType.type,
        workspace=builder.workspace,
        context=builder,
    )
    pages = []
    for page in PageHandler().get_pages(builder):
        if page.shared:
            continue
        elements = ElementService().get_elements(endpoint.user, page)
        pages.append(
            {
                "page_id": page.id,
                "name": page.name,
                "path": page.path,
                "elements": [
                    {"id": element.id, "type": element.get_type().type}
                    for element in elements
                ],
            }
        )
    return pages


class CreatePageInput(BaseModel):
    application_id: int = Field(..., description="The builder application.")
    name: str = Field(..., description="The page name.")
    path: str = Field(
        ...,
        description="The URL path, unique in the app, e.g. / or /customers. A "
        "detail page takes a parameter: /customer/:id.",
    )


def _path_params(path: str) -> list[dict]:
    """The parameters a path declares: ``:id`` and ``:x_id`` are numbers."""

    import re

    return [
        {
            "name": name,
            "type": "numeric" if name == "id" or name.endswith("_id") else "text",
        }
        for name in re.findall(r":([A-Za-z0-9_]+)", path)
    ]


def create_page(endpoint: SanadEndpoint, args: CreatePageInput) -> dict:
    from jadawel.contrib.builder.pages.service import PageService

    builder = get_application(endpoint, args.application_id, "builder")
    path = args.path if args.path.startswith("/") else f"/{args.path}"
    params = _path_params(path)
    page = PageService().create_page(
        endpoint.user, builder, args.name, path, path_params=params or None
    )
    result = {
        "page_id": page.id,
        "application_id": builder.id,
        "name": page.name,
        "path": page.path,
    }
    if params:
        result["read_parameters_with"] = [
            f"get('page_parameter.{param['name']}')" for param in params
        ]
    return result


class DeletePageInput(BaseModel):
    page_id: int = Field(..., description="The page to delete.")


def delete_page(endpoint: SanadEndpoint, args: DeletePageInput) -> dict:
    from jadawel.contrib.builder.pages.service import PageService

    page = get_page(endpoint, args.page_id)
    PageService().delete_page(endpoint.user, page)
    return {"deleted_page_id": args.page_id}


class PageContent(BaseModel):
    type: Literal["heading", "text", "link", "image"]
    text: str = Field(
        "",
        description="Plain text: the heading, paragraph or link text, or an image's alt text.",
    )
    level: int = Field(2, ge=1, le=6, description="Heading level, 1 is largest.")
    markdown: bool = Field(False, description="Text only: render as Markdown.")
    to_page_id: Optional[int] = Field(
        None, description="Link only: a page of the same app to open."
    )
    url: Optional[str] = Field(
        None, description="Link: an external URL. Image: the image URL."
    )
    as_button: bool = Field(False, description="Link only: show as a button.")


class AddPageContentInput(BaseModel):
    page_id: int = Field(..., description="The page to add to, at the end.")
    elements: list[PageContent] = Field(..., min_length=1)


def _content_values(item: PageContent) -> dict:
    if item.type == "heading":
        return {"value": formula_literal(item.text), "level": item.level}
    if item.type == "text":
        return {
            "value": formula_literal(item.text),
            "format": "markdown" if item.markdown else "plain",
        }
    if item.type == "link":
        values = {
            "value": formula_literal(item.text),
            "variant": "button" if item.as_button else "link",
        }
        if item.to_page_id:
            values.update(navigation_type="page", navigate_to_page_id=item.to_page_id)
        elif item.url:
            values.update(
                navigation_type="custom", navigate_to_url=formula_literal(item.url)
            )
        else:
            raise ValueError("A link needs to_page_id or url.")
        return values
    if not item.url:
        raise ValueError("An image needs url.")
    return {
        "image_source_type": "url",
        "image_url": formula_literal(item.url),
        "alt_text": formula_literal(item.text),
    }


def add_page_content(endpoint: SanadEndpoint, args: AddPageContentInput) -> dict:
    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService

    page = get_page(endpoint, args.page_id)
    for item in args.elements:
        if item.type == "link" and item.to_page_id:
            get_page(endpoint, item.to_page_id)
    created = []
    with transaction.atomic():
        for item in args.elements:
            element = ElementService().create_element(
                endpoint.user,
                element_type_registry.get(item.type),
                page,
                **_content_values(item),
            )
            created.append({"id": element.id, "type": item.type})
    return {
        "page_id": page.id,
        "application_id": page.builder_id,
        "elements": created,
    }


def _pick_fields(table, field_ids: Optional[list[int]], limit: int):
    """The requested fields in order, or the table's first ``limit`` fields."""

    fields = [
        field.specific for field in table.field_set.order_by("-primary", "order", "id")
    ]
    if not field_ids:
        return fields[:limit]
    by_id = {field.id: field for field in fields}
    missing = [field_id for field_id in field_ids if field_id not in by_id]
    if missing:
        raise ValueError(f"Fields {missing} are not in table {table.id}.")
    return [by_id[field_id] for field_id in field_ids]


def _field_type(field) -> str:
    from jadawel.contrib.database.fields.registries import field_type_registry

    return field_type_registry.get_by_model(field).type


MULTI_VALUE_FIELD_TYPES = ("multiple_select", "link_row", "multiple_collaborators")


def _table_column(field) -> dict:
    """A table element column that renders ``field`` readably."""

    path = f"current_record.{field.db_column}"
    kind = _field_type(field)
    if kind == "boolean":
        return {
            "name": field.name,
            "type": "boolean",
            "config": {"value": f"get('{path}')"},
        }
    if kind in MULTI_VALUE_FIELD_TYPES:
        return {
            "name": field.name,
            "type": "tags",
            "config": {"values": f"get('{path}.*.value')"},
        }
    if kind == "single_select":
        return {
            "name": field.name,
            "type": "text",
            "config": {"value": f"get('{path}.value')"},
        }
    return {"name": field.name, "type": "text", "config": {"value": f"get('{path}')"}}


class AddTableToPageInput(BaseModel):
    page_id: int = Field(..., description="The page to add the table to.")
    table_id: int = Field(..., description="The database table to show.")
    field_ids: Optional[list[int]] = Field(
        None, description="Columns to show, in order. Omit for the first 8 fields."
    )
    title: Optional[str] = Field(None, description="A heading above the table.")
    items_per_page: int = Field(20, ge=1, le=100)


def add_table_to_page(endpoint: SanadEndpoint, args: AddTableToPageInput) -> dict:
    from jadawel.contrib.builder.data_sources.service import DataSourceService
    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService
    from jadawel.contrib.database.mcp import services
    from jadawel.core.services.registries import service_type_registry

    page = get_page(endpoint, args.page_id)
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    fields = _pick_fields(table, args.field_ids, limit=8)
    with transaction.atomic():
        integration = local_integration(endpoint, page.builder)
        data_source = DataSourceService().create_data_source(
            endpoint.user,
            page,
            service_type_registry.get("local_jadawel_list_rows"),
            name=data_source_name(page, args.title or table.name),
            table_id=table.id,
            integration_id=integration.id,
        )
        element_service = ElementService()
        if args.title:
            element_service.create_element(
                endpoint.user,
                element_type_registry.get("heading"),
                page,
                value=formula_literal(args.title),
                level=2,
            )
        element = element_service.create_element(
            endpoint.user,
            element_type_registry.get("table"),
            page,
            data_source_id=data_source.id,
            items_per_page=args.items_per_page,
            fields=[_table_column(field) for field in fields],
        )
    return {
        "page_id": page.id,
        "application_id": page.builder_id,
        "table_element_id": element.id,
        "data_source_id": data_source.id,
        "columns": [field.name for field in fields],
    }


def data_source_name(page, proposed: str) -> str:
    """``proposed``, numbered if the page already has a data source by that name."""

    from jadawel.contrib.builder.data_sources.handler import DataSourceHandler

    return DataSourceHandler().find_unused_data_source_name(page, proposed[:200])


def _link_row_input(endpoint: SanadEndpoint, page, integration, field):
    """A dropdown of the linked table's rows, for a link-to-table field.

    Its options come from a list-rows data source on the linked table, as the
    editor's "formula" options do: each option's value is the row ID, which the
    create-row action links, and its label is the row's primary field.
    """

    from django.conf import settings

    from jadawel.contrib.builder.data_sources.service import DataSourceService
    from jadawel.contrib.builder.elements.models import ChoiceElement
    from jadawel.contrib.database.fields.models import Field
    from jadawel.core.services.registries import service_type_registry

    linked = field.link_row_table
    primary = Field.objects.filter(table=linked, primary=True).first()
    data_source = DataSourceService().create_data_source(
        endpoint.user,
        page,
        service_type_registry.get("local_jadawel_list_rows"),
        name=data_source_name(page, f"{field.name} ({linked.name})"),
        table_id=linked.id,
        integration_id=integration.id,
        # A dropdown shows every option at once, so ask for the most rows allowed.
        default_result_count=settings.INTEGRATION_LOCAL_JADAWEL_PAGE_SIZE_LIMIT,
    )
    rows = f"data_source.{data_source.id}.*"
    return "choice", {
        "label": formula_literal(field.name),
        "show_as_dropdown": True,
        "multiple": field.link_row_multiple_relationships,
        "option_type": ChoiceElement.OPTION_TYPE.FORMULAS,
        "formula_value": f"get('{rows}.id')",
        "formula_name": (
            f"get('{rows}.field_{primary.id}')" if primary else f"get('{rows}.id')"
        ),
    }


def _form_input(field) -> Optional[tuple[str, dict]]:
    """The input element for ``field``, or None when forms cannot set it.

    Link-to-table fields are handled by ``_link_row_input``, which needs a page.
    """

    kind = _field_type(field)
    label = {"label": formula_literal(field.name)}
    if kind in ("text", "url", "phone_number"):
        return "input_text", label
    if kind == "email":
        return "input_text", {**label, "validation_type": "email"}
    if kind == "long_text":
        return "input_text", {**label, "is_multiline": True, "rows": 4}
    if kind == "number":
        integer = (field.number_decimal_places or 0) == 0
        return "input_text", {
            **label,
            "validation_type": "integer" if integer else "any",
        }
    if kind == "rating":
        return "input_text", {**label, "validation_type": "integer"}
    if kind == "boolean":
        return "checkbox", label
    if kind == "date":
        return "datetime_picker", {
            **label,
            "date_format": field.date_format,
            "include_time": field.date_include_time,
        }
    if kind == "single_select":
        options = [
            {"name": option.value, "value": option.value}
            for option in field.select_options.order_by("order", "id")
        ]
        return "choice", {**label, "options": options, "show_as_dropdown": True}
    return None


def _add_form_inputs(endpoint, page, integration, form, fields, required_ids):
    """Add an input for each field to ``form``: ``([(field, element)], skipped)``.

    :raises ValueError: when none of ``fields`` can be filled in by a form.
    """

    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService

    mapped, skipped = [], []
    for field in fields:
        if _field_type(field) == "link_row":
            spec = _link_row_input(endpoint, page, integration, field)
        else:
            spec = _form_input(field)
        if spec is None:
            skipped.append(field.name)
            continue
        element_type, values = spec
        element = ElementService().create_element(
            endpoint.user,
            element_type_registry.get(element_type),
            page,
            parent_element_id=form.id,
            required=field.id in required_ids,
            **values,
        )
        mapped.append((field, element))
    if not mapped:
        raise ValueError("None of these fields can be filled in by a form.")
    return mapped, skipped


class AddFormToPageInput(BaseModel):
    page_id: int = Field(..., description="The page to add the form to.")
    table_id: int = Field(..., description="The table each submission adds a row to.")
    field_ids: Optional[list[int]] = Field(
        None, description="Fields to ask for, in order. Omit for every writable field."
    )
    required_field_ids: list[int] = Field(
        default_factory=list, description="Fields the visitor must fill in."
    )
    title: Optional[str] = Field(None, description="A heading above the form.")
    submit_label: str = Field("Submit", description="The submit button text.")
    success_message: str = Field(
        "Saved", description="The notification shown after a submission."
    )


def add_form_to_page(endpoint: SanadEndpoint, args: AddFormToPageInput) -> dict:
    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService
    from jadawel.contrib.builder.workflow_actions.models import EventTypes
    from jadawel.contrib.builder.workflow_actions.registries import (
        builder_workflow_action_type_registry,
    )
    from jadawel.contrib.builder.workflow_actions.service import (
        BuilderWorkflowActionService,
    )
    from jadawel.contrib.database.fields.registries import field_type_registry
    from jadawel.contrib.database.mcp import services

    page = get_page(endpoint, args.page_id)
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    writable = [
        field
        for field in _pick_fields(table, args.field_ids, limit=50)
        if not field_type_registry.get_by_model(field).read_only
    ]
    elements = ElementService()
    with transaction.atomic():
        integration = local_integration(endpoint, page.builder)
        if args.title:
            elements.create_element(
                endpoint.user,
                element_type_registry.get("heading"),
                page,
                value=formula_literal(args.title),
                level=2,
            )
        form = elements.create_element(
            endpoint.user,
            element_type_registry.get("form_container"),
            page,
            submit_button_label=formula_literal(args.submit_label),
        )
        mapped, skipped = _add_form_inputs(
            endpoint, page, integration, form, writable, args.required_field_ids
        )
        created_inputs = [
            {"id": element.id, "field": field.name} for field, element in mapped
        ]

        # The row a submission creates, attached to the form's submit event.
        # The service is passed as values, as the editor sends it, so the
        # upsert-row type validates the table against the user's permissions.
        row_service = {
            "table_id": table.id,
            "integration_id": integration.id,
            "field_mappings": [
                {
                    "field_id": field.id,
                    "enabled": True,
                    "value": f"get('form_data.{element.id}')",
                }
                for field, element in mapped
            ],
        }
        actions = BuilderWorkflowActionService()
        actions.create_workflow_action(
            endpoint.user,
            builder_workflow_action_type_registry.get("create_row"),
            page,
            service=row_service,
            element=form,
            event=EventTypes.SUBMIT,
        )
        actions.create_workflow_action(
            endpoint.user,
            builder_workflow_action_type_registry.get("notification"),
            page,
            title=formula_literal(args.success_message),
            element=form,
            event=EventTypes.SUBMIT,
        )
    return {
        "page_id": page.id,
        "application_id": page.builder_id,
        "form_element_id": form.id,
        "inputs": created_inputs,
        "skipped_fields": skipped,
    }


class AddFieldsToFormInput(BaseModel):
    form_element_id: int = Field(
        ..., description="The form to extend (form_element_id from add_form_to_page)."
    )
    field_ids: list[int] = Field(
        ..., description="Fields of the form's table to ask for, in order."
    )
    required_field_ids: list[int] = Field(
        default_factory=list, description="Fields the visitor must fill in."
    )


def add_fields_to_form(endpoint: SanadEndpoint, args: AddFieldsToFormInput) -> dict:
    from jadawel.contrib.builder.elements.service import ElementService
    from jadawel.contrib.builder.workflow_actions.models import (
        BuilderWorkflowAction,
    )
    from jadawel.contrib.builder.workflow_actions.service import (
        BuilderWorkflowActionService,
    )
    from jadawel.contrib.database.fields.registries import field_type_registry

    form = ElementService().get_element(endpoint.user, args.form_element_id).specific
    page = get_page(endpoint, form.page_id)
    if form.get_type().type != "form_container":
        raise ValueError(f"Element {form.id} is not a form.")
    create_rows = [
        action.specific
        for action in BuilderWorkflowAction.objects.filter(element=form)
        if action.get_type().type == "create_row"
    ]
    if len(create_rows) != 1:
        raise ValueError(
            "The form must save its submissions with one create-row action."
        )
    action = create_rows[0]
    service = action.service.specific
    existing = list(service.field_mappings.all())
    already = {mapping.field_id for mapping in existing if mapping.enabled}
    fields = [
        field
        for field in _pick_fields(service.table, args.field_ids, limit=50)
        if field.id not in already
        and not field_type_registry.get_by_model(field).read_only
    ]
    if not fields:
        raise ValueError("The form already asks for every one of these fields.")

    with transaction.atomic():
        mapped, skipped = _add_form_inputs(
            endpoint,
            page,
            local_integration(endpoint, page.builder),
            form,
            fields,
            args.required_field_ids,
        )
        new_ids = {field.id for field, _ in mapped}
        BuilderWorkflowActionService().update_workflow_action(
            endpoint.user,
            action,
            service={
                "field_mappings": [
                    {
                        "field_id": mapping.field_id,
                        "enabled": mapping.enabled,
                        "value": mapping.value,
                    }
                    for mapping in existing
                    if mapping.field_id not in new_ids
                ]
                + [
                    {
                        "field_id": field.id,
                        "enabled": True,
                        "value": f"get('form_data.{element.id}')",
                    }
                    for field, element in mapped
                ]
            },
        )
    return {
        "page_id": page.id,
        "application_id": page.builder_id,
        "form_element_id": form.id,
        "inputs": [
            {"id": element.id, "field": field.name} for field, element in mapped
        ],
        "skipped_fields": skipped,
    }


def get_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "create_builder_application",
            "Create an application-builder app (web pages, portals, forms). "
            "It starts with no pages.",
            CreateBuilderApplicationInput,
            create_builder_application,
        ),
        SanadTool(
            "list_pages",
            "List a builder app's pages and the elements on each.",
            ListPagesInput,
            list_pages,
        ),
        SanadTool(
            "create_page",
            "Add a page to a builder app.",
            CreatePageInput,
            create_page,
        ),
        SanadTool(
            "delete_page",
            "Delete a builder page. Needs the user's approval.",
            DeletePageInput,
            delete_page,
        ),
        SanadTool(
            "add_page_content",
            "Append headings, paragraphs, links (to a page or URL, optionally "
            "as buttons) and images to a page. Give plain text, not formulas.",
            AddPageContentInput,
            add_page_content,
        ),
        SanadTool(
            "add_table_to_page",
            "Show a database table's rows on a page as a table.",
            AddTableToPageInput,
            add_table_to_page,
        ),
        SanadTool(
            "add_form_to_page",
            "Add a form to a page; each submission creates a row in a table. "
            "Link-to-table fields become a dropdown of the linked table's rows.",
            AddFormToPageInput,
            add_form_to_page,
        ),
        SanadTool(
            "add_fields_to_form",
            "Ask for more fields in an existing form, and save them with its "
            "submissions. Link-to-table fields become a dropdown of the linked "
            "table's rows.",
            AddFieldsToFormInput,
            add_fields_to_form,
        ),
    ]
