from typing import Any, Callable, Dict, Iterable, Optional

from django.contrib.auth.models import AbstractUser
from django.db import router
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from jadawel.contrib.automation.nodes.exceptions import (
    AutomationNodeFirstNodeMustBeTrigger,
    AutomationNodeMisconfiguredService,
    AutomationNodeNotDeletable,
    AutomationNodeNotMovable,
    AutomationNodeNotReplaceable,
    AutomationNodeTriggerAlreadyExists,
    AutomationNodeTriggerMustBeFirstNode,
)
from jadawel.contrib.automation.nodes.models import (
    AIAgentActionNode,
    AutomationNode,
    AutomationTriggerNode,
    CoreHTTPRequestActionNode,
    CoreHTTPTriggerNode,
    CoreIteratorActionNode,
    CorePeriodicTriggerNode,
    CoreResponseActionNode,
    CoreRouterActionNode,
    CoreSMTPEmailActionNode,
    LocalJadawelAggregateRowsActionNode,
    LocalJadawelCreateRowActionNode,
    LocalJadawelDeleteRowActionNode,
    LocalJadawelGetRowActionNode,
    LocalJadawelListRowsActionNode,
    LocalJadawelRowsCreatedTriggerNode,
    LocalJadawelRowsDeletedTriggerNode,
    LocalJadawelRowsUpdatedTriggerNode,
    LocalJadawelUpdateRowActionNode,
    SlackWriteMessageActionNode,
)
from jadawel.contrib.automation.nodes.registries import AutomationNodeType
from jadawel.contrib.automation.nodes.types import NodePositionType
from jadawel.contrib.automation.workflows.constants import WorkflowState
from jadawel.contrib.automation.workflows.models import AutomationWorkflow
from jadawel.contrib.integrations.ai.service_types import AIAgentServiceType
from jadawel.contrib.integrations.core.service_types import (
    CoreHTTPRequestServiceType,
    CoreHTTPTriggerServiceType,
    CoreIteratorServiceType,
    CorePeriodicServiceType,
    CoreResponseServiceType,
    CoreRouterServiceType,
    CoreSMTPEmailServiceType,
)
from jadawel.contrib.integrations.local_jadawel.service_types import (
    LocalJadawelAggregateRowsUserServiceType,
    LocalJadawelDeleteRowServiceType,
    LocalJadawelGetRowUserServiceType,
    LocalJadawelListRowsUserServiceType,
    LocalJadawelRowsCreatedServiceType,
    LocalJadawelRowsDeletedServiceType,
    LocalJadawelRowsUpdatedServiceType,
    LocalJadawelUpsertRowServiceType,
)
from jadawel.contrib.integrations.slack.service_types import (
    SlackWriteMessageServiceType,
)
from jadawel.core.formula.types import (
    JADAWEL_FORMULA_MODE_RAW,
    JadawelFormulaObject,
)
from jadawel.core.registry import Instance
from jadawel.core.services.models import Service
from jadawel.core.services.registries import service_type_registry


class AutomationNodeActionNodeType(AutomationNodeType):
    is_workflow_action = True

    def before_create(self, workflow, reference_node, position, output):
        if reference_node is None:
            raise AutomationNodeFirstNodeMustBeTrigger()

    def before_move(self, node, reference_node, position, output):
        if reference_node is None:
            raise AutomationNodeFirstNodeMustBeTrigger()


class ContainerNodeTypeMixin:
    is_container = True

    def before_delete(self, node: "ContainerNodeTypeMixin"):
        if node.workflow.get_graph().get_children(node):
            raise AutomationNodeNotDeletable(
                "Container nodes cannot be deleted if they "
                "have one or more children nodes associated with them."
            )

    def before_replace(self, node: "ContainerNodeTypeMixin", new_node_type: Instance):
        if node.workflow.get_graph().get_children(node):
            raise AutomationNodeNotReplaceable(
                "Container nodes cannot be replaced if they "
                "have one or more children nodes associated with them."
            )

        super().before_replace(node, new_node_type)

    def before_move(
        self,
        node: "ContainerNodeTypeMixin",
        reference_node: AutomationNode | None,
        position: NodePositionType,
        output: str,
    ):
        """
        Check the container node is not moved inside itself.
        """

        if node in reference_node.get_parent_nodes():
            raise AutomationNodeNotMovable(
                "A container node cannot be moved inside itself"
            )

        super().before_move(node, reference_node, position, output)


class LocalJadawelUpsertRowNodeType(AutomationNodeActionNodeType):
    type = "local_jadawel_upsert_row"
    compat_type = "upsert_row"
    service_type = LocalJadawelUpsertRowServiceType.type

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_local_jadawel_upsert_row_service()
        return {"service": service}


class LocalJadawelCreateRowNodeType(LocalJadawelUpsertRowNodeType):
    type = "local_jadawel_create_row"
    compat_type = "create_row"
    model_class = LocalJadawelCreateRowActionNode


class LocalJadawelUpdateRowNodeType(LocalJadawelUpsertRowNodeType):
    type = "local_jadawel_update_row"
    compat_type = "update_row"
    model_class = LocalJadawelUpdateRowActionNode


class LocalJadawelDeleteRowNodeType(AutomationNodeActionNodeType):
    type = "local_jadawel_delete_row"
    compat_type = "delete_row"
    model_class = LocalJadawelDeleteRowActionNode
    service_type = LocalJadawelDeleteRowServiceType.type


class LocalJadawelGetRowNodeType(AutomationNodeActionNodeType):
    type = "local_jadawel_get_row"
    compat_type = "get_row"
    model_class = LocalJadawelGetRowActionNode
    service_type = LocalJadawelGetRowUserServiceType.type


class LocalJadawelListRowsNodeType(AutomationNodeActionNodeType):
    type = "local_jadawel_list_rows"
    compat_type = "list_rows"
    model_class = LocalJadawelListRowsActionNode
    service_type = LocalJadawelListRowsUserServiceType.type


class LocalJadawelAggregateRowsNodeType(AutomationNodeActionNodeType):
    type = "local_jadawel_aggregate_rows"
    compat_type = "aggregate_rows"
    model_class = LocalJadawelAggregateRowsActionNode
    service_type = LocalJadawelAggregateRowsUserServiceType.type


class CoreHttpRequestNodeType(AutomationNodeActionNodeType):
    type = "http_request"
    model_class = CoreHTTPRequestActionNode
    service_type = CoreHTTPRequestServiceType.type


class CoreIteratorNodeType(ContainerNodeTypeMixin, AutomationNodeActionNodeType):
    type = "iterator"
    model_class = CoreIteratorActionNode
    service_type = CoreIteratorServiceType.type


class CoreSMTPEmailNodeType(AutomationNodeActionNodeType):
    type = "smtp_email"
    model_class = CoreSMTPEmailActionNode
    service_type = CoreSMTPEmailServiceType.type


class CoreResponseNodeType(AutomationNodeActionNodeType):
    type = "response"
    model_class = CoreResponseActionNode
    service_type = CoreResponseServiceType.type

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: AutomationNode = None,
    ) -> Dict[str, Any]:
        """Default new response nodes to a raw 204 status-code formula."""

        if instance is None:
            service_values = values.get("service") or {}
            values = {
                **values,
                "service": {
                    "status_code": JadawelFormulaObject.create(
                        "204", mode=JADAWEL_FORMULA_MODE_RAW
                    ),
                    **service_values,
                },
            }
        return super().prepare_values(values, user, instance)


class AIAgentActionNodeType(AutomationNodeActionNodeType):
    type = "ai_agent"
    model_class = AIAgentActionNode
    service_type = AIAgentServiceType.type


class CoreRouterActionNodeType(AutomationNodeActionNodeType):
    type = "router"
    model_class = CoreRouterActionNode
    service_type = CoreRouterServiceType.type

    def has_node_on_edge(self, node: CoreRouterActionNode) -> bool:
        """
        Given a router node, this method returns whether one of its edges has a node.

        :param node: The router node instance.
        """

        for edge_uid in node.service.get_type().get_edges(node.service.specific).keys():
            if edge_uid != "" and node.workflow.get_graph().get_next_nodes(
                node, edge_uid
            ):
                return True

        return False

    def before_delete(self, node: CoreRouterActionNode):
        if self.has_node_on_edge(node):
            raise AutomationNodeNotDeletable(
                "Router nodes cannot be deleted if they "
                "have one or more output nodes associated with them."
            )

        super().before_delete(node)

    def before_replace(self, node: CoreRouterActionNode, new_node_type: Instance):
        if self.has_node_on_edge(node):
            raise AutomationNodeNotReplaceable(
                "Router nodes cannot be replaced if they "
                "have one or more output nodes associated with them."
            )

        super().before_replace(node, new_node_type)

    def before_move(
        self,
        node: AutomationTriggerNode,
        reference_node: AutomationNode | None,
        position: NodePositionType,
        output: str,
    ):
        """
        Check the container node is not moved inside it self.
        """

        if self.has_node_on_edge(node):
            raise AutomationNodeNotMovable(
                "Router nodes cannot be moved if they "
                "have one or more output nodes associated with them."
            )

        super().before_move(node, reference_node, position, output)

    def after_create(self, node: CoreRouterActionNode):
        """
        After a router node is created, this method will create
        an initial edge for the user to start with.

        :param node: The router node instance that was just created.
        """

        if not len(node.service.edges.all()):
            node.service.edges.create(label=_("Branch"))

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: AutomationNode = None,
    ) -> Dict[str, Any]:
        """
        Before updating a router node's service, this method is called to allow us to
        check if one or more edges have been removed. If so, we need to verify that
        there are no automation node outputs pointing to those edges. If there are,
        then an exception is raised to prevent the update.

        :param values: The values to prepare for the router node.
        :param user: The user performing the action.
        :param instance: The current instance of the router node.
        :return: The prepared values for the router node.
        """

        service_values = values.get("service", {})
        if instance and "edges" in service_values:
            prepared_uids = [
                str(edge["uid"]) for edge in service_values.get("edges", [])
            ]
            service = instance.service.specific
            persisted_uids = [str(edge.uid) for edge in service.edges.only("uid")]
            removed_uids = list(set(persisted_uids) - set(prepared_uids))

            for removed_uid in removed_uids:
                if instance.workflow.get_graph().get_node_at_position(
                    instance, "south", removed_uid
                ):
                    raise AutomationNodeMisconfiguredService(
                        "One or more branches have been removed from the router node, "
                        "but they still point to output nodes. These nodes must be "
                        "trashed before the router can be updated."
                    )

        return super().prepare_values(values, user, instance)


class AutomationNodeTriggerType(AutomationNodeType):
    is_workflow_trigger = True

    def after_register(self):
        service_type_registry.get(self.service_type).start_listening(self.on_event)
        return super().after_register()

    def before_unregister(self):
        service_type_registry.get(self.service_type).stop_listening()
        return super().before_unregister()

    def before_create(
        self,
        workflow: AutomationWorkflow,
        reference_node: AutomationNode,
        position: str,
        output: str,
    ):
        if workflow.get_graph().get_node_at_position(None, "south", ""):
            raise AutomationNodeTriggerAlreadyExists()

        if reference_node is not None:
            raise AutomationNodeTriggerMustBeFirstNode()

    def before_delete(self, node: AutomationNode):
        if node.workflow.get_graph().get_next_nodes(node):
            raise AutomationNodeNotDeletable(
                "Trigger nodes cannot be deleted if they are followed nodes."
            )

    def before_move(
        self,
        node: AutomationTriggerNode,
        reference_node: AutomationNode | None,
        position: NodePositionType,
        output: str,
    ):
        raise AutomationNodeNotMovable("Trigger nodes cannot be moved.")

    def on_event(
        self,
        services: Iterable[Service],
        event_payload: Dict | None | Callable = None,
        user: Optional[AbstractUser] = None,
    ):
        from jadawel.contrib.automation.workflows.handler import (
            AutomationWorkflowHandler,
        )

        triggers = list(
            self.model_class.objects.filter(
                service__in=services,
            )
            .using(router.db_for_write(self.model_class))
            .filter(
                Q(
                    Q(workflow__state=WorkflowState.LIVE)
                    | Q(workflow__allow_test_run_until__gte=timezone.now())
                    | Q(workflow__simulate_until_node__isnull=False)
                ),
            )
            .select_related("workflow__automation__workspace")
        )

        # For perf reasons, store the trigger<->service relationship.
        service_map = {service.id: service for service in services}

        histories = []
        for trigger in triggers:
            # If we've received a callable payload, call it with the specific service,
            # this can give us a payload that is specific to the trigger's service.
            service_payload = (
                event_payload(service_map[trigger.service_id])
                if callable(event_payload)
                else event_payload
            )

            workflow = trigger.workflow
            history = AutomationWorkflowHandler().async_start_workflow(
                workflow,
                service_payload,
            )
            if history is not None:
                histories.append(history)

            # We don't want subsequent events to trigger a new test run
            AutomationWorkflowHandler().reset_workflow_temporary_states(workflow)

        return histories


class LocalJadawelRowsCreatedNodeTriggerType(AutomationNodeTriggerType):
    type = "local_jadawel_rows_created"
    compat_type = "rows_created"
    model_class = LocalJadawelRowsCreatedTriggerNode
    service_type = LocalJadawelRowsCreatedServiceType.type


class LocalJadawelRowsUpdatedNodeTriggerType(AutomationNodeTriggerType):
    type = "local_jadawel_rows_updated"
    compat_type = "rows_updated"
    model_class = LocalJadawelRowsUpdatedTriggerNode
    service_type = LocalJadawelRowsUpdatedServiceType.type


class LocalJadawelRowsDeletedNodeTriggerType(AutomationNodeTriggerType):
    type = "local_jadawel_rows_deleted"
    compat_type = "rows_deleted"
    model_class = LocalJadawelRowsDeletedTriggerNode
    service_type = LocalJadawelRowsDeletedServiceType.type


class CorePeriodicTriggerNodeType(
    AutomationNodeTriggerType,
):
    type = "periodic"
    model_class = CorePeriodicTriggerNode
    service_type = CorePeriodicServiceType.type


class CoreHTTPTriggerNodeType(AutomationNodeTriggerType):
    type = "http_trigger"
    model_class = CoreHTTPTriggerNode
    service_type = CoreHTTPTriggerServiceType.type


class SlackWriteMessageActionNodeType(AutomationNodeActionNodeType):
    type = "slack_write_message"
    model_class = SlackWriteMessageActionNode
    service_type = SlackWriteMessageServiceType.type
