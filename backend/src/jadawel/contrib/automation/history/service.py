from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from jadawel.contrib.automation.history.exceptions import (
    AutomationWorkflowHistoryDoesNotExist,
)
from jadawel.contrib.automation.history.handler import AutomationHistoryHandler
from jadawel.contrib.automation.history.models import AutomationWorkflowHistory
from jadawel.contrib.automation.workflows.handler import AutomationWorkflowHandler
from jadawel.contrib.automation.workflows.operations import (
    ReadAutomationWorkflowOperationType,
    UpdateAutomationWorkflowOperationType,
)
from jadawel.contrib.automation.workflows.signals import (
    automation_workflow_dispatch_cancellation_requested,
)
from jadawel.core.handler import CoreHandler


class AutomationHistoryService:
    def __init__(self):
        self.handler = AutomationHistoryHandler()
        self.workflow_handler = AutomationWorkflowHandler()

    def get_workflow_histories(
        self, user: AbstractUser, workflow_id: int
    ) -> QuerySet[AutomationWorkflowHistory]:
        """
        Returns an AutomationWorkflowHistory queryset related to a workflow.

        :param user: The user requesting the workflow history.
        :param workflow_id: The ID of the workflow.
        :return: A queryset of workflow histories.
        """

        workflow = self.workflow_handler.get_workflow(workflow_id)

        CoreHandler().check_permissions(
            user,
            ReadAutomationWorkflowOperationType.type,
            workspace=workflow.automation.workspace,
            context=workflow,
        )

        return self.handler.get_workflow_histories(workflow)

    def request_cancellation(
        self, user: AbstractUser, workflow_history_id: int
    ) -> AutomationWorkflowHistory:
        """
        Requests the cancellation of a running workflow history.

        Whoever can update the workflow can cancel its runs. Runs execute against
        the published clone, so the permission is checked against the editable
        `original_workflow`.

        :param user: The user requesting the cancellation.
        :param workflow_history_id: The id of the run to cancel.
        :raises AutomationWorkflowHistoryDoesNotExist: If the run doesn't exist or
            is a simulation run.
        :raises AutomationWorkflowHistoryNotRunning: If the run already resolved.
        :raises AutomationWorkflowHistoryCancellationAlreadyRequested: If the
            cancellation of the run was already requested.
        :return: The refreshed workflow history.
        """

        workflow_history = self.handler.get_workflow_history(
            workflow_history_id,
            base_queryset=AutomationWorkflowHistory.objects.select_related(
                "original_workflow__automation__workspace"
            ),
        )

        if workflow_history.simulate_until_node_id is not None:
            raise AutomationWorkflowHistoryDoesNotExist(workflow_history_id)

        workflow = workflow_history.original_workflow
        CoreHandler().check_permissions(
            user,
            UpdateAutomationWorkflowOperationType.type,
            workspace=workflow.automation.workspace,
            context=workflow,
        )

        workflow_history = self.handler.request_workflow_history_cancellation(
            workflow_history, user
        )

        automation_workflow_dispatch_cancellation_requested.send(
            self, workflow_history=workflow_history, user=user
        )

        return workflow_history
