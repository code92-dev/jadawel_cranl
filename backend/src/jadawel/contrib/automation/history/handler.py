import time
from datetime import datetime
from typing import Dict, List, Optional, Union

from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from jadawel.contrib.automation.history.constants import HistoryStatusChoices
from jadawel.contrib.automation.history.exceptions import (
    AutomationWorkflowHistoryCancellationAlreadyRequested,
    AutomationWorkflowHistoryDoesNotExist,
    AutomationWorkflowHistoryNodeResultDoesNotExist,
    AutomationWorkflowHistoryNotRunning,
)
from jadawel.contrib.automation.history.models import (
    AutomationNodeHistory,
    AutomationNodeResult,
    AutomationWorkflowHistory,
    AutomationWorkflowHistoryResponse,
)
from jadawel.contrib.automation.nodes.models import AutomationNode
from jadawel.contrib.automation.workflows.models import AutomationWorkflow
from jadawel.contrib.integrations.core.constants import RESPONSE_BODY_TYPE


class AutomationHistoryHandler:
    RESPONSE_POLL_INITIAL_INTERVAL_SECONDS = 0.1
    RESPONSE_POLL_MAX_INTERVAL_SECONDS = 1.0
    RESPONSE_POLL_BACKOFF_MULTIPLIER = 2

    def get_workflow_histories(
        self, workflow: AutomationWorkflow, base_queryset: Optional[QuerySet] = None
    ) -> QuerySet[AutomationWorkflowHistory]:
        """
        Returns all the AutomationWorkflowHistory related to the provided workflow.

        Excludes any simulation histories that haven't yet been deleted.
        """

        if base_queryset is None:
            base_queryset = AutomationWorkflowHistory.objects.all()

        return base_queryset.filter(
            original_workflow=workflow,
            simulate_until_node__isnull=True,
        ).prefetch_related(
            Prefetch(
                "node_histories",
                queryset=AutomationNodeHistory.objects.select_related(
                    "node", "node__workflow"
                )
                .prefetch_related("node_results")
                .order_by("started_on"),
            ),
        )

    def get_workflow_history(
        self, history_id: int, base_queryset: Optional[QuerySet] = None
    ) -> AutomationWorkflowHistory:
        """
        Returns a AutomationWorkflowHistory by its ID.

        :param history_id: The ID of the AutomationWorkflowHistory.
        :param base_queryset: Can be provided to already filter or apply performance
            improvements to the queryset when it's being executed.
        :raises AutomationWorkflowHistoryDoesNotExist: If the history doesn't exist.
        :return: The model instance of the AutomationWorkflowHistory
        """

        if base_queryset is None:
            base_queryset = AutomationWorkflowHistory.objects.all()

        try:
            return base_queryset.select_related(
                "workflow__automation__workspace", "cancellation_requested_by"
            ).get(id=history_id)
        except AutomationWorkflowHistory.DoesNotExist:
            raise AutomationWorkflowHistoryDoesNotExist(history_id)

    def create_workflow_history(
        self,
        original_workflow: AutomationWorkflow,
        workflow: AutomationWorkflow,
        started_on: datetime,
        is_test_run: bool,
        event_payload: Optional[Union[Dict, List[Dict]]] = None,
        simulate_until_node: Optional[AutomationNode] = None,
        status: HistoryStatusChoices = HistoryStatusChoices.STARTED,
        completed_on: Optional[datetime] = None,
        message: str = "",
    ) -> AutomationWorkflowHistory:
        """Creates a history entry for a Workflow run."""

        return AutomationWorkflowHistory.objects.create(
            workflow=workflow,
            original_workflow=original_workflow,
            started_on=started_on,
            is_test_run=is_test_run,
            simulate_until_node=simulate_until_node,
            event_payload=event_payload,
            status=status,
            completed_on=completed_on,
            message=message,
        )

    def request_workflow_history_cancellation(
        self, workflow_history: AutomationWorkflowHistory, user: AbstractUser
    ) -> AutomationWorkflowHistory:
        """
        Records that `user` asked for the given run to be cancelled.

        This is the first phase of a cooperative cancellation: nothing is stopped
        here. The runner reads the request fields before dispatching every node and
        finalizes the run itself, see `finalize_workflow_history_cancellation`.

        The update is conditional so that it never clobbers a run that has just
        reached a terminal status, and so that only the first request is recorded:
        a later one is refused and keeps the attribution of the first requester,
        which tells that later requester somebody else asked before them.

        :param workflow_history: The run to cancel.
        :param user: The user requesting the cancellation.
        :raises AutomationWorkflowHistoryNotRunning: If the run already resolved.
        :raises AutomationWorkflowHistoryCancellationAlreadyRequested: If the
            cancellation of the run was already requested.
        :return: The refreshed workflow history.
        """

        updated = AutomationWorkflowHistory.objects.filter(
            id=workflow_history.id,
            status=HistoryStatusChoices.STARTED,
            cancellation_requested_on__isnull=True,
        ).update(
            cancellation_requested_by=user,
            cancellation_requested_on=timezone.now(),
        )

        # Whether we won the update or not, the row decides the outcome: a run that
        # already resolved is an error even if our request landed first. A run that
        # is still running but wasn't updated was already flagged by someone else.
        workflow_history = self.get_workflow_history(workflow_history.id)
        if workflow_history.status != HistoryStatusChoices.STARTED:
            raise AutomationWorkflowHistoryNotRunning(workflow_history.id)
        if not updated:
            raise AutomationWorkflowHistoryCancellationAlreadyRequested(
                workflow_history.id
            )

        return workflow_history

    def finalize_workflow_history_cancellation(
        self, workflow_history: AutomationWorkflowHistory
    ) -> bool:
        """
        Marks a run whose cancellation was requested as `CANCELLED`.

        Called by the runner when it notices the cancellation request before
        dispatching a node. The update is guarded on the run still being `STARTED`
        so that it is idempotent: it never overwrites a run that was resolved in
        the meantime (e.g. by the timeout sweep or the dispatch-done handler), and
        it stays safe if dispatches within a run ever execute concurrently.

        :param workflow_history: The run to finalize.
        :return: True if this call performed the finalization.
        """

        # requester can be None if the user's account was deleted.
        requester = workflow_history.cancellation_requested_by
        if requester is not None:
            message = f"Cancelled by {requester.first_name} ({requester.id})."
        else:
            message = "Cancelled."

        updated = AutomationWorkflowHistory.objects.filter(
            id=workflow_history.id,
            status=HistoryStatusChoices.STARTED,
        ).update(
            status=HistoryStatusChoices.CANCELLED,
            completed_on=timezone.now(),
            message=message,
        )
        return updated == 1

    def create_node_history(
        self,
        workflow_history: AutomationWorkflowHistory,
        node: AutomationNode,
        started_on: datetime,
        status: HistoryStatusChoices = HistoryStatusChoices.STARTED,
        completed_on: Optional[datetime] = None,
        message: str = "",
    ) -> AutomationNodeHistory:
        """Creates a history entry for a Node dispatch."""

        return AutomationNodeHistory.objects.create(
            workflow_history=workflow_history,
            node=node,
            started_on=started_on,
            status=status,
            completed_on=completed_on,
            message=message,
        )

    def create_node_result(
        self,
        node_history: AutomationNodeHistory,
        result: Optional[Union[Dict, List[Dict]]] = None,
        iteration_path: str = "",
    ) -> AutomationNodeResult:
        """Saves the result of a Node dispatch."""

        result = result if result else {}
        return AutomationNodeResult.objects.create(
            node_history=node_history,
            iteration_path=iteration_path,
            result=result,
        )

    def get_node_result(self, history, node, iteration_path):
        """
        Returns the result for the given history/node/iteration_path.
        """

        try:
            node_result = AutomationNodeResult.objects.only("result").get(
                node_history__workflow_history_id=history.id,
                node_history__node_id=node.id,
                iteration_path=iteration_path,
            )
        except AutomationNodeResult.DoesNotExist:
            raise AutomationWorkflowHistoryNodeResultDoesNotExist()

        return node_result.result

    def create_workflow_history_response(
        self,
        workflow_history: AutomationWorkflowHistory,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body=None,
        body_type: str = RESPONSE_BODY_TYPE.EMPTY,
        source_node: Optional[AutomationNode] = None,
        is_default: bool = False,
    ) -> tuple[AutomationWorkflowHistoryResponse, bool]:
        """
        Creates the workflow response if one doesn't already exist.
        """

        try:
            with transaction.atomic():
                return (
                    AutomationWorkflowHistoryResponse.objects.create(
                        workflow_history=workflow_history,
                        status_code=status_code,
                        headers=headers or {},
                        body=body,
                        body_type=body_type,
                        source_node=source_node,
                        is_default=is_default,
                    ),
                    True,
                )
        except IntegrityError:
            return (
                AutomationWorkflowHistoryResponse.objects.get(
                    workflow_history=workflow_history
                ),
                False,
            )

    def ensure_default_response(
        self, workflow_history: AutomationWorkflowHistory
    ) -> AutomationWorkflowHistoryResponse:
        """
        Ensures the workflow history has a default empty 204 response.
        """

        response, _ = self.create_workflow_history_response(
            workflow_history,
            status_code=204,
            headers={},
            body=None,
            body_type=RESPONSE_BODY_TYPE.EMPTY,
            is_default=True,
        )
        return response

    def get_workflow_history_response(
        self, workflow_history: AutomationWorkflowHistory
    ) -> Optional[AutomationWorkflowHistoryResponse]:
        try:
            return AutomationWorkflowHistoryResponse.objects.get(
                workflow_history=workflow_history
            )
        except AutomationWorkflowHistoryResponse.DoesNotExist:
            return None

    def wait_for_workflow_response(
        self,
        workflow_history: AutomationWorkflowHistory,
        timeout_seconds: int,
    ) -> Optional[AutomationWorkflowHistoryResponse]:
        """
        Polls with bounded backoff until a response exists or the timeout expires.
        """

        deadline = time.monotonic() + timeout_seconds
        poll_interval = self.RESPONSE_POLL_INITIAL_INTERVAL_SECONDS
        while time.monotonic() < deadline:
            workflow_history.refresh_from_db(fields=["status", "completed_on"])
            if response := self.get_workflow_history_response(workflow_history):
                return response

            if workflow_history.status != HistoryStatusChoices.STARTED:
                return self.ensure_default_response(workflow_history)

            remaining_seconds = deadline - time.monotonic()
            if remaining_seconds <= 0:
                break

            time.sleep(min(poll_interval, remaining_seconds))
            poll_interval = min(
                poll_interval * self.RESPONSE_POLL_BACKOFF_MULTIPLIER,
                self.RESPONSE_POLL_MAX_INTERVAL_SECONDS,
            )

        return None
