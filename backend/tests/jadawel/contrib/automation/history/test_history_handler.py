from django.utils import timezone

import pytest
from freezegun import freeze_time

from jadawel.contrib.automation.history.constants import HistoryStatusChoices
from jadawel.contrib.automation.history.exceptions import (
    AutomationWorkflowHistoryCancellationAlreadyRequested,
    AutomationWorkflowHistoryDoesNotExist,
    AutomationWorkflowHistoryNotRunning,
)
from jadawel.contrib.automation.history.handler import AutomationHistoryHandler
from jadawel.contrib.automation.history.models import AutomationWorkflowHistory
from jadawel.contrib.automation.workflows.constants import WorkflowState


@pytest.mark.django_db
def test_get_workflow_histories_no_base_queryset(data_fixture):
    workflow = data_fixture.create_automation_workflow()

    result = AutomationHistoryHandler().get_workflow_histories(workflow)

    # Should return an empty queryset, since this workflow has no history
    assert list(result) == []


@pytest.mark.django_db
def test_get_workflow_histories_with_base_queryset(data_fixture):
    workflow = data_fixture.create_automation_workflow()

    result = AutomationHistoryHandler().get_workflow_histories(
        workflow, AutomationWorkflowHistory.objects.all()
    )

    # Should return an empty queryset, since this workflow has no history
    assert list(result) == []


@pytest.mark.django_db
def test_get_workflow_histories_returns_ordered_histories(data_fixture):
    original_workflow = data_fixture.create_automation_workflow()
    history_1 = data_fixture.create_workflow_history(
        original_workflow=original_workflow
    )
    history_2 = data_fixture.create_workflow_history(
        original_workflow=original_workflow
    )

    result = AutomationHistoryHandler().get_workflow_histories(original_workflow)

    # Ensure latest is returned first
    assert list(result) == [history_2, history_1]


@pytest.mark.django_db
def test_create_workflow_history(data_fixture):
    original_workflow = data_fixture.create_automation_workflow()
    published_workflow = data_fixture.create_automation_workflow(
        state=WorkflowState.LIVE
    )
    published_workflow.automation.published_from = original_workflow
    published_workflow.automation.save()

    now = timezone.now()
    history = AutomationHistoryHandler().create_workflow_history(
        original_workflow,
        original_workflow,
        now,
        False,
    )

    assert isinstance(history, AutomationWorkflowHistory)
    assert history.workflow == original_workflow


@pytest.mark.django_db
def test_get_workflow_histories_excludes_simulation_histories(data_fixture):
    """
    Simulation histories are deleted by the dispatch_node() once the final
    node is dispatched. However, we want to ensure they're excluded so that
    a user doesn't accidentally see them while the simulation is running.
    """

    workflow = data_fixture.create_automation_workflow()
    trigger = workflow.get_trigger()

    simulation_history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        simulate_until_node=trigger,
    )

    result = AutomationHistoryHandler().get_workflow_histories(workflow)

    assert len(result) == 0


@pytest.mark.django_db
def test_get_workflow_history(data_fixture):
    workflow = data_fixture.create_automation_workflow()
    history = AutomationHistoryHandler().create_workflow_history(
        workflow,
        workflow,
        timezone.now(),
        False,
    )

    result = AutomationHistoryHandler().get_workflow_history(history_id=history.id)

    assert result == history


@pytest.mark.django_db
def test_get_workflow_history_does_not_exist(data_fixture):
    with pytest.raises(AutomationWorkflowHistoryDoesNotExist) as e:
        AutomationHistoryHandler().get_workflow_history(history_id=100)

    assert str(e.value) == "The automation workflow history 100 does not exist."


@pytest.mark.django_db
def test_get_workflow_history_respects_base_queryset(data_fixture):
    workflow = data_fixture.create_automation_workflow()
    history = AutomationHistoryHandler().create_workflow_history(
        workflow,
        workflow,
        timezone.now(),
        False,
    )

    with pytest.raises(AutomationWorkflowHistoryDoesNotExist) as e:
        AutomationHistoryHandler().get_workflow_history(
            history_id=history.id,
            base_queryset=AutomationWorkflowHistory.objects.exclude(id=history.id),
        )


@pytest.mark.django_db
def test_get_workflow_history_prefetches_cancellation_requester(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        cancellation_requested_by=user,
        cancellation_requested_on=timezone.now(),
    )

    result = AutomationHistoryHandler().get_workflow_history(history_id=history.id)

    with django_assert_num_queries(0):
        assert result.cancellation_requested_by == user


@pytest.mark.django_db
def test_request_workflow_history_cancellation(data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    with freeze_time("2026-08-18 12:00:00"):
        result = AutomationHistoryHandler().request_workflow_history_cancellation(
            history, user
        )

    # Nothing is stopped yet: the run stays STARTED until the runner notices.
    assert result.id == history.id
    assert result.status == HistoryStatusChoices.STARTED
    assert result.completed_on is None
    assert result.cancellation_requested_by == user
    assert result.cancellation_requested_on.isoformat() == "2026-08-18T12:00:00+00:00"

    history.refresh_from_db()
    assert history.cancellation_requested_by == user
    assert history.cancellation_requested_on == result.cancellation_requested_on


@pytest.mark.django_db
def test_request_workflow_history_cancellation_already_requested(data_fixture):
    """
    A second request is refused so the requester knows somebody else asked
    first, and it must not clobber the attribution of the first one.
    """

    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )
    handler = AutomationHistoryHandler()

    with freeze_time("2026-08-18 12:00:00"):
        first = handler.request_workflow_history_cancellation(history, user)

    with freeze_time("2026-08-18 12:05:00"):
        with pytest.raises(AutomationWorkflowHistoryCancellationAlreadyRequested) as e:
            handler.request_workflow_history_cancellation(history, user_2)

    assert str(e.value) == (
        f"The cancellation of the automation workflow history {history.id} "
        "was already requested."
    )

    history.refresh_from_db()
    assert history.status == HistoryStatusChoices.STARTED
    assert history.cancellation_requested_by == user
    assert history.cancellation_requested_on == first.cancellation_requested_on


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        HistoryStatusChoices.SUCCESS,
        HistoryStatusChoices.ERROR,
        HistoryStatusChoices.CANCELLED,
    ],
)
def test_request_workflow_history_cancellation_not_running(data_fixture, status):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=status, completed_on=timezone.now()
    )

    with pytest.raises(AutomationWorkflowHistoryNotRunning) as e:
        AutomationHistoryHandler().request_workflow_history_cancellation(history, user)

    assert str(e.value) == (
        f"The automation workflow history {history.id} is not running."
    )

    # The resolved run is left untouched.
    history.refresh_from_db()
    assert history.status == status
    assert history.cancellation_requested_by is None
    assert history.cancellation_requested_on is None


@pytest.mark.django_db
def test_finalize_workflow_history_cancellation(data_fixture):
    user = data_fixture.create_user(first_name="Ada")
    workflow = data_fixture.create_automation_workflow(user=user)
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        cancellation_requested_by=user,
        cancellation_requested_on=timezone.now(),
    )

    with freeze_time("2026-08-18 12:00:00"):
        finalized = AutomationHistoryHandler().finalize_workflow_history_cancellation(
            history
        )

    assert finalized is True

    history.refresh_from_db()
    assert history.status == HistoryStatusChoices.CANCELLED
    assert history.message == f"Cancelled by Ada ({user.id})."
    assert history.completed_on.isoformat() == "2026-08-18T12:00:00+00:00"


@pytest.mark.django_db
def test_finalize_workflow_history_cancellation_without_requester(data_fixture):
    """
    The requester is `SET_NULL` so it can be gone if the account was deleted.
    """

    workflow = data_fixture.create_automation_workflow()
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        cancellation_requested_by=None,
        cancellation_requested_on=timezone.now(),
    )

    finalized = AutomationHistoryHandler().finalize_workflow_history_cancellation(
        history
    )

    assert finalized is True

    history.refresh_from_db()
    assert history.status == HistoryStatusChoices.CANCELLED
    assert history.message == "Cancelled."
    assert history.completed_on is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        HistoryStatusChoices.SUCCESS,
        HistoryStatusChoices.ERROR,
        HistoryStatusChoices.CANCELLED,
    ],
)
def test_finalize_workflow_history_cancellation_already_resolved(data_fixture, status):
    """
    Finalizing is idempotent and never overwrites a run that resolved in the
    meantime, e.g. by the timeout sweep or the dispatch-done handler.
    """

    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    completed_on = timezone.now()
    history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=status,
        message="original message",
        completed_on=completed_on,
        cancellation_requested_by=user,
        cancellation_requested_on=timezone.now(),
    )

    finalized = AutomationHistoryHandler().finalize_workflow_history_cancellation(
        history
    )

    assert finalized is False

    history.refresh_from_db()
    assert history.status == status
    assert history.message == "original message"
    assert history.completed_on == completed_on
