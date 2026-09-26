"""Sanad's tools for automations and application-builder apps.

Everything goes through the same permission-checked services and action types
the editors use, so Sanad can only build what the chatting user could build by
hand. Automation step settings are validated by each step type's own request
serializer (the one ``PATCH /api/automation/node/<id>/`` uses), so a setting
the UI would reject is rejected here too, with the same message.

Builder tools are deliberately higher level than the element API. A page is
assembled from a few intents — content, a table of rows, a form that saves a
row — and each one creates the data source, elements and workflow actions it
needs, following ``BuilderApplicationTypeInitApplication``.
"""

from typing import Literal, Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools import SanadEndpoint

LOCAL_INTEGRATION_NAME = "جداول المحلي"
"""What core names the integration it creates for a new app; matching it keeps
Sanad-built apps indistinguishable from hand-built ones."""


def formula_literal(text: str) -> str:
    """A formula that evaluates to exactly ``text``."""

    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------


def _application_type(application) -> str:
    from jadawel.core.registries import application_type_registry

    return application_type_registry.get_by_model(application.specific_class).type


def _get_application(endpoint: SanadEndpoint, application_id: int, expected: str):
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
    kind = _application_type(application)
    if kind != expected:
        raise ValueError(f"Application {application_id} is a {kind}, not a {expected}.")
    return application.specific


class ListApplicationsInput(BaseModel):
    type: Optional[str] = Field(
        None,
        description="Only list this type: database, builder, automation or dashboard.",
    )


def list_applications(endpoint: SanadEndpoint, args: ListApplicationsInput):
    from jadawel.core.handler import CoreHandler
    from jadawel.core.models import Application
    from jadawel.core.operations import ListApplicationsWorkspaceOperationType

    queryset = CoreHandler().filter_queryset(
        endpoint.user,
        ListApplicationsWorkspaceOperationType.type,
        Application.objects.filter(
            workspace=endpoint.workspace, trashed=False
        ).order_by("order", "id"),
        workspace=endpoint.workspace,
    )
    applications = [
        {"id": app.id, "name": app.name, "type": _application_type(app)}
        for app in queryset.select_related("content_type")
    ]
    if args.type:
        applications = [app for app in applications if app["type"] == args.type]
    return applications


# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------

STEP_DESCRIPTIONS = {
    "local_jadawel_rows_created": "Trigger: rows are created in a table.",
    "local_jadawel_rows_updated": "Trigger: rows are updated in a table.",
    "local_jadawel_rows_deleted": "Trigger: rows are deleted from a table.",
    "periodic": "Trigger: runs on a schedule (every minute, hour, day, week or month).",
    "http_trigger": "Trigger: an incoming HTTP request (webhook) to a unique URL.",
    "local_jadawel_create_row": "Action: create a row in a table.",
    "local_jadawel_update_row": "Action: update a row in a table.",
    "local_jadawel_delete_row": "Action: delete a row from a table.",
    "local_jadawel_get_row": "Action: read one row from a table.",
    "local_jadawel_list_rows": "Action: read several rows from a table.",
    "local_jadawel_aggregate_rows": "Action: sum, count, average… a field.",
    "http_request": "Action: send an HTTP request to an external URL.",
    "smtp_email": "Action: send an email (needs an SMTP connection).",
    "slack_write_message": "Action: post a Slack message (needs a Slack connection).",
    "ai_agent": "Action: ask an AI model (needs an AI connection).",
    "router": "Action: branch the workflow on conditions.",
    "iterator": "Action: repeat the following steps for each item of a list.",
}

AUTOMATION_FORMULA_NOTES = [
    "Every text-like setting is a formula. Literal text must be quoted: "
    "'Hello'. Combine with concat('New: ', get('previous_node.<id>.0.field_<field id>')).",
    "Row triggers output a list of rows: get('previous_node.<trigger id>.0.field_<field id>') "
    "reads a field of the first changed row; single steps such as get_row "
    "output one object: get('previous_node.<id>.field_<field id>').",
    "field_mappings items are {field_id, value, enabled: true}; value is a formula.",
    "integration_id is filled in automatically when the automation has exactly "
    "one connection of the needed kind.",
]


def _serialize_step(node) -> dict:
    from jadawel.contrib.automation.api.nodes.serializers import (
        AutomationNodeSerializer,
    )
    from jadawel.contrib.automation.nodes.registries import (
        automation_node_type_registry,
    )

    data = automation_node_type_registry.get_serializer(
        node, AutomationNodeSerializer
    ).data
    service = {
        key: value
        for key, value in dict(data["service"] or {}).items()
        if key not in ("schema", "context_data", "context_data_schema", "sample_data")
    }
    return {
        "id": data["id"],
        "type": data["type"],
        "label": data["label"],
        "settings": service,
    }


def _describe_field(field) -> dict:
    from rest_framework import serializers

    from jadawel.core.formula.serializers import FormulaSerializerField

    info = {"help": str(field.help_text or "")}
    if isinstance(field, FormulaSerializerField):
        info["type"] = "formula"
    elif isinstance(field, serializers.ChoiceField):
        info["type"] = "choice"
        info["choices"] = list(field.choices)
    elif isinstance(field, serializers.ListSerializer):
        info["type"] = "list"
        info["item"] = _describe_serializer(field.child)
    elif isinstance(field, serializers.BooleanField):
        info["type"] = "boolean"
    elif isinstance(field, serializers.IntegerField):
        info["type"] = "integer"
    elif isinstance(field, serializers.Serializer):
        info["type"] = "object"
        info["fields"] = _describe_serializer(field)
    else:
        info["type"] = "string"
    return info


def _describe_serializer(serializer) -> dict:
    return {
        name: _describe_field(field)
        for name, field in serializer.fields.items()
        if not field.read_only and name != "type"
    }


class DescribeAutomationStepInput(BaseModel):
    type: Optional[str] = Field(
        None,
        description="A step type to describe. Omit to list every step type.",
    )


def describe_automation_step(
    endpoint: SanadEndpoint, args: DescribeAutomationStepInput
) -> dict:
    from jadawel.contrib.automation.nodes.registries import (
        automation_node_type_registry,
    )

    if not args.type:
        return {
            "step_types": [
                {
                    "type": node_type.type,
                    "trigger": node_type.is_workflow_trigger,
                    "description": STEP_DESCRIPTIONS.get(node_type.type, ""),
                }
                for node_type in automation_node_type_registry.get_all()
            ]
        }
    node_type = automation_node_type_registry.get(args.type)
    service_type = node_type.get_service_type()
    serializer = service_type.get_serializer_class(request_serializer=True)()
    return {
        "type": node_type.type,
        "trigger": node_type.is_workflow_trigger,
        "description": STEP_DESCRIPTIONS.get(node_type.type, ""),
        "needs_connection": service_type.integration_type,
        "settings": _describe_serializer(serializer),
        "notes": AUTOMATION_FORMULA_NOTES,
    }


class CreateAutomationInput(BaseModel):
    name: str = Field(..., description="The automation's name.")
    workflow_name: Optional[str] = Field(
        None, description="A name for its first workflow."
    )


def create_automation(endpoint: SanadEndpoint, args: CreateAutomationInput) -> dict:
    from jadawel.contrib.automation.workflows.actions import (
        UpdateAutomationWorkflowActionType,
    )
    from jadawel.contrib.automation.workflows.models import AutomationWorkflow
    from jadawel.core.actions import CreateApplicationActionType
    from jadawel.core.integrations.models import Integration

    with transaction.atomic():
        # `init_with_data` is what the "add new" menu sends: it gives the
        # automation its first workflow and a local data connection.
        automation = CreateApplicationActionType.do(
            endpoint.user,
            endpoint.workspace,
            "automation",
            name=args.name,
            init_with_data=True,
        )
        workflow = (
            AutomationWorkflow.objects.filter(automation=automation)
            .order_by("order", "id")
            .first()
        )
        if args.workflow_name:
            workflow = UpdateAutomationWorkflowActionType.do(
                endpoint.user, workflow.id, {"name": args.workflow_name}
            )
        integration = Integration.objects.filter(application=automation).first()
    return {
        "automation_id": automation.id,
        "name": automation.name,
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "integration_id": integration.id if integration else None,
    }


class CreateWorkflowInput(BaseModel):
    automation_id: int = Field(..., description="The automation to add it to.")
    name: str = Field(..., description="The workflow's name.")


def create_workflow(endpoint: SanadEndpoint, args: CreateWorkflowInput) -> dict:
    from jadawel.contrib.automation.workflows.actions import (
        CreateAutomationWorkflowActionType,
    )

    automation = _get_application(endpoint, args.automation_id, "automation")
    workflow = CreateAutomationWorkflowActionType.do(
        endpoint.user, automation.id, {"name": args.name}
    )
    return {
        "automation_id": automation.id,
        "workflow_id": workflow.id,
        "name": workflow.name,
    }


def _get_workflow(endpoint: SanadEndpoint, workflow_id: int):
    from jadawel.contrib.automation.workflows.exceptions import (
        AutomationWorkflowDoesNotExist,
    )
    from jadawel.contrib.automation.workflows.service import (
        AutomationWorkflowService,
    )

    workflow = AutomationWorkflowService().get_workflow(endpoint.user, workflow_id)
    if workflow.automation.workspace_id != endpoint.workspace.id:
        raise AutomationWorkflowDoesNotExist(workflow_id)
    return workflow


def _get_step(endpoint: SanadEndpoint, node_id: int):
    from jadawel.contrib.automation.nodes.exceptions import (
        AutomationNodeDoesNotExist,
    )
    from jadawel.contrib.automation.nodes.service import AutomationNodeService

    node = AutomationNodeService().get_node(endpoint.user, node_id)
    if node.workflow.automation.workspace_id != endpoint.workspace.id:
        raise AutomationNodeDoesNotExist(node_id)
    return node


class GetWorkflowInput(BaseModel):
    workflow_id: int = Field(..., description="The workflow to read.")


def get_workflow(endpoint: SanadEndpoint, args: GetWorkflowInput) -> dict:
    from jadawel.contrib.automation.api.workflows.serializers import (
        AutomationWorkflowSerializer,
    )
    from jadawel.contrib.automation.nodes.service import AutomationNodeService

    workflow = _get_workflow(endpoint, args.workflow_id)
    steps = AutomationNodeService().get_nodes(endpoint.user, workflow)
    # The editor's own serializer: state and publish date live on the separate
    # published copy of the workflow, which it resolves.
    published = AutomationWorkflowSerializer(workflow).data
    return {
        "workflow_id": workflow.id,
        "automation_id": workflow.automation_id,
        "name": workflow.name,
        "state": published["state"],
        "published_on": published["published_on"],
        "graph": workflow.graph,
        "steps": [_serialize_step(step) for step in steps],
    }


def _apply_step_settings(
    endpoint: SanadEndpoint, node, label: Optional[str], settings: dict
):
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.automation.api.nodes.serializers import (
        UpdateAutomationNodeSerializer,
    )
    from jadawel.contrib.automation.application_types import (
        AutomationApplicationType,
    )
    from jadawel.contrib.automation.nodes.actions import (
        UpdateAutomationNodeActionType,
    )
    from jadawel.contrib.automation.nodes.registries import (
        automation_node_type_registry,
    )

    node_type = automation_node_type_registry.get_by_model(node.specific_class)
    payload = {}
    if label is not None:
        payload["label"] = label
    if settings:
        payload["service"] = {
            **settings,
            "type": node_type.get_service_type().type,
        }
    if not payload:
        return node
    data = validate_data_custom_fields(
        node_type.type,
        automation_node_type_registry,
        payload,
        base_serializer_class=UpdateAutomationNodeSerializer,
        serializer_class_context={"application_type": AutomationApplicationType},
        partial=True,
        return_validated=True,
    )
    return UpdateAutomationNodeActionType.do(endpoint.user, node.id, data)


class AddAutomationStepInput(BaseModel):
    workflow_id: int = Field(..., description="The workflow to add the step to.")
    type: str = Field(
        ...,
        description="The step type. Call describe_automation_step to list them.",
    )
    after_step_id: Optional[int] = Field(
        None,
        description=(
            "The step this one runs after. Omit only for the trigger, which "
            "must be the first step."
        ),
    )
    branch: Optional[str] = Field(
        None,
        description="After a router: the uid of the router edge this step follows.",
    )
    label: Optional[str] = Field(None, description="A short name for the step.")
    settings: dict = Field(
        default_factory=dict,
        description=(
            "The step's settings, exactly as describe_automation_step lists "
            "them (for example table_id, field_mappings, interval)."
        ),
    )


def add_automation_step(endpoint: SanadEndpoint, args: AddAutomationStepInput):
    from jadawel.contrib.automation.nodes.actions import (
        CreateAutomationNodeActionType,
    )
    from jadawel.contrib.automation.nodes.registries import (
        automation_node_type_registry,
    )

    workflow = _get_workflow(endpoint, args.workflow_id)
    node_type = automation_node_type_registry.get(args.type)
    placement = {}
    if args.after_step_id is not None:
        placement = {"reference_node_id": args.after_step_id, "position": "south"}
        if args.branch:
            placement["output"] = args.branch
    with transaction.atomic():
        node = CreateAutomationNodeActionType.do(
            endpoint.user, node_type, workflow, placement
        )
        node = _apply_step_settings(endpoint, node, args.label, args.settings)
    return {
        **_serialize_step(node),
        "workflow_id": workflow.id,
        "automation_id": workflow.automation_id,
    }


class UpdateAutomationStepInput(BaseModel):
    step_id: int = Field(..., description="The step to change.")
    label: Optional[str] = Field(None, description="A new short name.")
    settings: dict = Field(
        default_factory=dict,
        description="Only the settings to change; the rest are kept.",
    )


def update_automation_step(endpoint: SanadEndpoint, args: UpdateAutomationStepInput):
    node = _get_step(endpoint, args.step_id)
    node = _apply_step_settings(endpoint, node, args.label, args.settings)
    return {
        **_serialize_step(node),
        "workflow_id": node.workflow_id,
        "automation_id": node.workflow.automation_id,
    }


class DeleteAutomationStepInput(BaseModel):
    step_id: int = Field(..., description="The step to delete.")


def delete_automation_step(endpoint: SanadEndpoint, args: DeleteAutomationStepInput):
    from jadawel.contrib.automation.nodes.actions import (
        DeleteAutomationNodeActionType,
    )

    node = _get_step(endpoint, args.step_id)
    DeleteAutomationNodeActionType.do(endpoint.user, node.id)
    return {"deleted_step_id": args.step_id}


class PublishWorkflowInput(BaseModel):
    workflow_id: int = Field(..., description="The workflow to publish.")


def publish_workflow(endpoint: SanadEndpoint, args: PublishWorkflowInput) -> dict:
    from jadawel.contrib.automation.workflows.service import (
        AutomationWorkflowService,
    )

    workflow = _get_workflow(endpoint, args.workflow_id)
    job = AutomationWorkflowService().async_publish(endpoint.user, workflow.id)
    return {
        "workflow_id": workflow.id,
        "automation_id": workflow.automation_id,
        "publish_job_id": job.id,
        "status": "publishing; the workflow goes live in a few seconds",
    }


# ---------------------------------------------------------------------------
# Application builder
# ---------------------------------------------------------------------------


def _local_integration(endpoint: SanadEndpoint, builder):
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
        integration = _local_integration(endpoint, builder)
    return {
        "application_id": builder.id,
        "name": builder.name,
        "integration_id": integration.id,
    }


def _get_page(endpoint: SanadEndpoint, page_id: int):
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

    builder = _get_application(endpoint, args.application_id, "builder")
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
        ..., description="The URL path, unique in the app, e.g. / or /customers."
    )


def create_page(endpoint: SanadEndpoint, args: CreatePageInput) -> dict:
    from jadawel.contrib.builder.pages.service import PageService

    builder = _get_application(endpoint, args.application_id, "builder")
    path = args.path if args.path.startswith("/") else f"/{args.path}"
    page = PageService().create_page(endpoint.user, builder, args.name, path)
    return {
        "page_id": page.id,
        "application_id": builder.id,
        "name": page.name,
        "path": page.path,
    }


class DeletePageInput(BaseModel):
    page_id: int = Field(..., description="The page to delete.")


def delete_page(endpoint: SanadEndpoint, args: DeletePageInput) -> dict:
    from jadawel.contrib.builder.pages.service import PageService

    page = _get_page(endpoint, args.page_id)
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

    page = _get_page(endpoint, args.page_id)
    for item in args.elements:
        if item.type == "link" and item.to_page_id:
            _get_page(endpoint, item.to_page_id)
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

    page = _get_page(endpoint, args.page_id)
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    fields = _pick_fields(table, args.field_ids, limit=8)
    with transaction.atomic():
        integration = _local_integration(endpoint, page.builder)
        data_source = DataSourceService().create_data_source(
            endpoint.user,
            page,
            service_type_registry.get("local_jadawel_list_rows"),
            name=args.title or table.name,
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


def _form_input(field) -> Optional[tuple[str, dict]]:
    """The input element for ``field``, or None when forms cannot set it."""

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

    page = _get_page(endpoint, args.page_id)
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    writable = [
        field
        for field in _pick_fields(table, args.field_ids, limit=50)
        if not field_type_registry.get_by_model(field).read_only
    ]
    elements = ElementService()
    created_inputs, skipped = [], []
    with transaction.atomic():
        integration = _local_integration(endpoint, page.builder)
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
        mapped = []
        for field in writable:
            spec = _form_input(field)
            if spec is None:
                skipped.append(field.name)
                continue
            element_type, values = spec
            element = elements.create_element(
                endpoint.user,
                element_type_registry.get(element_type),
                page,
                parent_element_id=form.id,
                required=field.id in args.required_field_ids,
                **values,
            )
            mapped.append((field, element))
            created_inputs.append({"id": element.id, "field": field.name})
        if not mapped:
            raise ValueError("None of these fields can be filled in by a form.")

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
