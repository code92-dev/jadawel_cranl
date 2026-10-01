from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jadawel.api.decorators import map_exceptions
from jadawel.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from jadawel.contrib.automation.api.history.errors import (
    ERROR_AUTOMATION_WORKFLOW_HISTORY_CANCELLATION_ALREADY_REQUESTED,
    ERROR_AUTOMATION_WORKFLOW_HISTORY_DOES_NOT_EXIST,
    ERROR_AUTOMATION_WORKFLOW_HISTORY_NOT_RUNNING,
)
from jadawel.contrib.automation.api.workflows.serializers import (
    AutomationWorkflowHistorySerializer,
)
from jadawel.contrib.automation.history.exceptions import (
    AutomationWorkflowHistoryCancellationAlreadyRequested,
    AutomationWorkflowHistoryDoesNotExist,
    AutomationWorkflowHistoryNotRunning,
)
from jadawel.contrib.automation.history.service import AutomationHistoryService

AUTOMATION_HISTORY_TAG = "Automation history"


class CancelAutomationWorkflowHistoryView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workflow_history_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workflow history to cancel.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=[AUTOMATION_HISTORY_TAG],
        operation_id="cancel_automation_workflow_history",
        description=(
            "Requests the cancellation of a running workflow. The run stops before "
            "the next node is dispatched; the node currently running is not "
            "interrupted. If the run completes before the cancellation takes "
            "effect, it resolves as completed. Only the first request is "
            "recorded: a later one is refused so that the requester is known "
            "precisely."
        ),
        request=None,
        responses={
            200: AutomationWorkflowHistorySerializer,
            400: get_error_schema(
                [
                    "ERROR_AUTOMATION_WORKFLOW_HISTORY_NOT_RUNNING",
                    "ERROR_AUTOMATION_WORKFLOW_HISTORY_CANCELLATION_ALREADY_REQUESTED",
                ]
            ),
            404: get_error_schema(["ERROR_AUTOMATION_WORKFLOW_HISTORY_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AutomationWorkflowHistoryDoesNotExist: (
                ERROR_AUTOMATION_WORKFLOW_HISTORY_DOES_NOT_EXIST
            ),
            AutomationWorkflowHistoryNotRunning: (
                ERROR_AUTOMATION_WORKFLOW_HISTORY_NOT_RUNNING
            ),
            AutomationWorkflowHistoryCancellationAlreadyRequested: (
                ERROR_AUTOMATION_WORKFLOW_HISTORY_CANCELLATION_ALREADY_REQUESTED
            ),
        }
    )
    def post(self, request, workflow_history_id: int):
        workflow_history = AutomationHistoryService().request_cancellation(
            request.user, workflow_history_id
        )
        serializer = AutomationWorkflowHistorySerializer(workflow_history)
        return Response(serializer.data)
