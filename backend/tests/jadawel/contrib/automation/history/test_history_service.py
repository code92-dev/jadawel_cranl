from unittest.mock import patch

from django.utils import timezone

import pytest

from jadawel.contrib.automation.history.constants import HistoryStatusChoices
from jadawel.contrib.automation.history.exceptions import (
    AutomationWorkflowHistoryCancellationAlreadyRequested,
    AutomationWorkflowHistoryDoesNotExist,
    AutomationWorkflowHistoryNotRunning,
)
from jadawel.contrib.automation.history.service import AutomationHistoryService
from jadawel.contrib.automation.workflows.constants import WorkflowState
from jadawel.core.exceptions import UserNotInWorkspace


@pytest.mark.django_db
def test_get_workflow_histories_permission_error(data_fixture):
    user = data_fixture.create_user()
    history = data_fixture.create_workflow_history(user=user)

    # Different user
    user_2 = data_fixture.create_user()

    with pytest.raises(UserNotInWorkspace) as e:
        AutomationHistoryService().get_workflow_histories(user_2, history.workflow.id)

    assert str(e.value) == (
        f"User {user_2.email} doesn't belong to "
        f"workspace {history.workflow.automation.workspace}."
    )


@pytest.mark.django_db
def test_get_workflow_histories_returns_ordered_histories(data_fixture):
    user = data_fixture.create_user()
    original_workflow = data_fixture.create_automation_workflow(user=user)

    history_1 = data_fixture.create_workflow_history(
        original_workflow=original_workflow
    )
    history_2 = data_fixture.create_workflow_history(
        original_workflow=original_workflow
    )

    result = AutomationHistoryService().get_workflow_histories(
        user, original_workflow.id
    )

    assert list(result) == [history_2, history_1]


SERVICES_PATH = "jadawel.contrib.automation.history.service"


@pytest.mark.django_db
def test_request_cancellation(data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    result = AutomationHistoryService().request_cancellation(user, history.id)

    assert result.id == history.id
    assert result.status == HistoryStatusChoices.STARTED
    assert result.cancellation_requested_by == user
    assert result.cancellation_requested_on is not None


@patch(f"{SERVICES_PATH}.automation_workflow_dispatch_cancellation_requested")
@pytest.mark.django_db
def test_request_cancellation_signal_sent(mock_signal, data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    service = AutomationHistoryService()
    result = service.request_cancellation(user, history.id)

    mock_signal.send.assert_called_once_with(
        service, workflow_history=result, user=user
    )


@patch(f"{SERVICES_PATH}.automation_workflow_dispatch_cancellation_requested")
@pytest.mark.django_db
def test_request_cancellation_signal_not_sent_when_already_requested(
    mock_signal, data_fixture
):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        cancellation_requested_by=user,
        cancellation_requested_on=timezone.now(),
    )

    with pytest.raises(AutomationWorkflowHistoryCancellationAlreadyRequested):
        AutomationHistoryService().request_cancellation(user, history.id)

    mock_signal.send.assert_not_called()


@patch(f"{SERVICES_PATH}.automation_workflow_dispatch_cancellation_requested")
@pytest.mark.django_db
def test_request_cancellation_signal_not_sent_when_not_running(
    mock_signal, data_fixture
):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.SUCCESS
    )

    with pytest.raises(AutomationWorkflowHistoryNotRunning):
        AutomationHistoryService().request_cancellation(user, history.id)

    mock_signal.send.assert_not_called()


@pytest.mark.django_db
def test_request_cancellation_permission_error(data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    user_2 = data_fixture.create_user()

    with pytest.raises(UserNotInWorkspace) as e:
        AutomationHistoryService().request_cancellation(user_2, history.id)

    assert str(e.value) == (
        f"User {user_2.email} doesn't belong to "
        f"workspace {workflow.automation.workspace}."
    )

    history.refresh_from_db()
    assert history.cancellation_requested_by is None
    assert history.cancellation_requested_on is None


@pytest.mark.django_db
def test_request_cancellation_checks_permissions_on_original_workflow(data_fixture):
    """
    Runs execute against the published clone, but the permission to cancel them
    is the permission to update the editable original workflow.
    """

    user = data_fixture.create_user()
    original_workflow = data_fixture.create_automation_workflow(user=user)
    # The published clone lives in a workspace the user has no access to, which
    # can't happen in practice but proves which workflow is checked.
    other_user = data_fixture.create_user()
    published_workflow = data_fixture.create_automation_workflow(
        user=other_user, state=WorkflowState.LIVE
    )
    published_workflow.automation.published_from = original_workflow
    published_workflow.automation.save()

    history = data_fixture.create_automation_workflow_history(
        workflow=published_workflow,
        original_workflow=original_workflow,
        status=HistoryStatusChoices.STARTED,
    )

    result = AutomationHistoryService().request_cancellation(user, history.id)

    assert result.cancellation_requested_by == user

    with pytest.raises(UserNotInWorkspace):
        AutomationHistoryService().request_cancellation(other_user, history.id)


@pytest.mark.django_db
def test_request_cancellation_does_not_exist(data_fixture):
    user = data_fixture.create_user()

    with pytest.raises(AutomationWorkflowHistoryDoesNotExist):
        AutomationHistoryService().request_cancellation(user, 999999)


@pytest.mark.django_db
def test_request_cancellation_simulation_run_does_not_exist(data_fixture):
    """
    Simulation runs are not visible in the history panel, so they are treated
    as non-existent rather than cancellable.
    """

    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        simulate_until_node=workflow.get_trigger(),
    )

    with pytest.raises(AutomationWorkflowHistoryDoesNotExist):
        AutomationHistoryService().request_cancellation(user, history.id)

    history.refresh_from_db()
    assert history.cancellation_requested_on is None


@pytest.mark.django_db
def test_request_cancellation_not_running(data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.SUCCESS,
        completed_on=timezone.now(),
    )

    with pytest.raises(AutomationWorkflowHistoryNotRunning):
        AutomationHistoryService().request_cancellation(user, history.id)
