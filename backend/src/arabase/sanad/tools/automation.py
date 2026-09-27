"""Sanad's automation tools: automations, workflows and their steps.

Everything goes through the same permission-checked services and action types
the editor uses, so Sanad can only build what the chatting user could build by
hand. Step settings are validated by each step type's own request serializer
(the one ``PATCH /api/automation/node/<id>/`` uses), so a setting the editor
would reject is rejected here too, with the same message.
"""

from typing import Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import (
    SanadEndpoint,
    SanadTool,
    describe_serializer,
    get_application,
)

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
    "Match each field_id to the field you mean: the step you get back names the "
    "field behind every mapping. A single select takes an existing option's "
    "exact text ('High'), a link to another table takes row IDs "
    "(get('previous_node.<trigger id>.0.id')).",
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
    _name_mapped_fields(service)
    return {
        "id": data["id"],
        "type": data["type"],
        "label": data["label"],
        "settings": service,
    }


def _name_mapped_fields(settings: dict) -> None:
    """Add each mapped field's name and type (and options) to its mapping.

    A mapping names its field by ID alone, so a model that picks the wrong ID
    (Priority for Assignee) could not see the mistake in the result.
    """

    mappings = settings.get("field_mappings") or []
    if not mappings:
        return

    from jadawel.contrib.database.fields.models import Field
    from jadawel.contrib.database.fields.registries import field_type_registry

    fields = Field.objects.filter(
        id__in=[mapping["field_id"] for mapping in mappings]
    ).prefetch_related("select_options")
    fields = {field.id: field for field in fields}
    for mapping in mappings:
        field = fields.get(mapping["field_id"])
        if field is None:
            continue
        field_type = field_type_registry.get_by_model(field.specific_class)
        mapping["field_name"] = field.name
        mapping["field_type"] = field_type.type
        if field_type.can_have_select_options:
            mapping["select_options"] = [
                option.value for option in field.select_options.all()
            ]


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
        "settings": describe_serializer(serializer),
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

    automation = get_application(endpoint, args.automation_id, "automation")
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
    if "edges" in settings:
        settings = {**settings, "edges": _router_edges(node, settings["edges"])}
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


def _router_edges(node, edges: list) -> list:
    """Router branches with their ``uid``, which the editor makes up itself.

    A branch given without one keeps the uid of the existing branch with the
    same label, so the steps attached to it stay attached; a new one gets a
    new uid.
    """

    import uuid

    existing = {}
    service = node.service.specific
    if hasattr(service, "edges"):
        existing = {edge.label: str(edge.uid) for edge in service.edges.all()}
    return [
        edge
        if not isinstance(edge, dict) or edge.get("uid")
        else {**edge, "uid": existing.get(edge.get("label")) or str(uuid.uuid4())}
        for edge in edges
    ]


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
    inside_step_id: Optional[int] = Field(
        None,
        description="An iterator step: make this the first step run for each "
        "item. Add the following ones with after_step_id.",
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
    if args.inside_step_id is not None:
        placement = {"reference_node_id": args.inside_step_id, "position": "child"}
    elif args.after_step_id is not None:
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


class GetWorkflowRunsInput(BaseModel):
    workflow_id: int = Field(
        ..., description="The workflow you built (not a published copy)."
    )
    limit: int = Field(5, ge=1, le=20, description="How many recent runs.")


def get_workflow_runs(endpoint: SanadEndpoint, args: GetWorkflowRunsInput) -> dict:
    from jadawel.contrib.automation.history.service import AutomationHistoryService
    from jadawel.contrib.automation.nodes.registries import (
        automation_node_type_registry,
    )

    workflow = _get_workflow(endpoint, args.workflow_id)
    runs = AutomationHistoryService().get_workflow_histories(
        endpoint.user, workflow.id
    )[: args.limit]
    return {
        "workflow_id": workflow.id,
        "automation_id": workflow.automation_id,
        "note": "started means queued or still running; check again shortly.",
        "runs": [
            {
                "status": run.status,
                "test_run": run.is_test_run,
                "started_on": run.started_on.isoformat(),
                "completed_on": run.completed_on and run.completed_on.isoformat(),
                "error": run.message,
                "steps": [
                    {
                        "type": automation_node_type_registry.get_by_model(
                            step.node.specific_class
                        ).type,
                        "label": step.node.label,
                        "status": step.status,
                        "error": step.message,
                    }
                    for step in run.node_histories.all()
                ],
            }
            for run in runs
        ],
    }


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


def get_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "create_automation",
            "Create an automation. It comes with a first, empty workflow and a "
            "connection to this workspace's tables; add steps to that workflow.",
            CreateAutomationInput,
            create_automation,
        ),
        SanadTool(
            "create_workflow",
            "Add another workflow to an existing automation.",
            CreateWorkflowInput,
            create_workflow,
        ),
        SanadTool(
            "describe_automation_step",
            "List the automation step types, or describe one type's settings. "
            "Call it before adding a step whose settings you do not know.",
            DescribeAutomationStepInput,
            describe_automation_step,
        ),
        SanadTool(
            "get_workflow",
            "Read a workflow: its steps, their settings and how they connec",
            GetWorkflowInput,
            get_workflow,
        ),
        SanadTool(
            "get_workflow_runs",
            "Read a workflow's latest runs: whether each succeeded and, if not, "
            "which step failed and why. Use it to check an automation works.",
            GetWorkflowRunsInput,
            get_workflow_runs,
        ),
        SanadTool(
            "add_automation_step",
            "Add a step to a workflow: first the trigger (no after_step_id), "
            "then each action after the previous step.",
            AddAutomationStepInput,
            add_automation_step,
        ),
        SanadTool(
            "update_automation_step",
            "Change a step's label or settings.",
            UpdateAutomationStepInput,
            update_automation_step,
        ),
        SanadTool(
            "delete_automation_step",
            "Delete a workflow step. Needs the user's approval.",
            DeleteAutomationStepInput,
            delete_automation_step,
        ),
        SanadTool(
            "publish_workflow",
            "Publish a workflow so it runs on real data. Needs the user's "
            "approval; build and review the steps firs",
            PublishWorkflowInput,
            publish_workflow,
        ),
    ]
