from django.urls import reverse
from django.utils import timezone

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from jadawel.contrib.automation.history.constants import HistoryStatusChoices
from tests.jadawel.contrib.automation.api.utils import get_api_kwargs

API_URL_CANCEL_WORKFLOW_HISTORY = "api:automation:history:cancel_workflow_history"


@pytest.mark.django_db
def test_cancel_workflow_history(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workflow = data_fixture.create_automation_workflow(user=user)
    workflow_history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY,
        kwargs={"workflow_history_id": workflow_history.id},
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == workflow_history.id
    # The run is only flagged: it stays running until the runner notices.
    assert response_json["status"] == "started"
    assert response_json["cancellation_requested_on"] is not None

    workflow_history.refresh_from_db()
    assert workflow_history.status == HistoryStatusChoices.STARTED
    assert workflow_history.cancellation_requested_by == user
    assert workflow_history.cancellation_requested_on is not None


@pytest.mark.django_db
def test_cancel_workflow_history_permission_error(api_client, data_fixture):
    user = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    workflow_history = data_fixture.create_automation_workflow_history(
        workflow=workflow, status=HistoryStatusChoices.STARTED
    )

    _, token = data_fixture.create_user_and_token()

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY,
        kwargs={"workflow_history_id": workflow_history.id},
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"

    workflow_history.refresh_from_db()
    assert workflow_history.cancellation_requested_on is None


@pytest.mark.django_db
def test_cancel_workflow_history_does_not_exist(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY, kwargs={"workflow_history_id": 999999}
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_404_NOT_FOUND
    assert (
        response.json()["error"] == "ERROR_AUTOMATION_WORKFLOW_HISTORY_DOES_NOT_EXIST"
    )


@pytest.mark.django_db
def test_cancel_workflow_history_simulation_run_does_not_exist(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    workflow = data_fixture.create_automation_workflow(user=user)
    workflow_history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        simulate_until_node=workflow.get_trigger(),
    )

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY,
        kwargs={"workflow_history_id": workflow_history.id},
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_404_NOT_FOUND
    assert (
        response.json()["error"] == "ERROR_AUTOMATION_WORKFLOW_HISTORY_DOES_NOT_EXIST"
    )


@pytest.mark.django_db
def test_cancel_workflow_history_not_running(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workflow = data_fixture.create_automation_workflow(user=user)
    workflow_history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.SUCCESS,
        completed_on=timezone.now(),
    )

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY,
        kwargs={"workflow_history_id": workflow_history.id},
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error": "ERROR_AUTOMATION_WORKFLOW_HISTORY_NOT_RUNNING",
        "detail": "The automation workflow history is not running anymore.",
    }


@pytest.mark.django_db
def test_cancel_workflow_history_already_requested(api_client, data_fixture):
    """
    A second client asking to cancel a run that somebody else already flagged is
    told so, and the attribution of the first requester is kept.
    """

    user, token = data_fixture.create_user_and_token()
    requester = data_fixture.create_user()
    workflow = data_fixture.create_automation_workflow(user=user)
    requested_on = timezone.now()
    workflow_history = data_fixture.create_automation_workflow_history(
        workflow=workflow,
        status=HistoryStatusChoices.STARTED,
        cancellation_requested_by=requester,
        cancellation_requested_on=requested_on,
    )

    url = reverse(
        API_URL_CANCEL_WORKFLOW_HISTORY,
        kwargs={"workflow_history_id": workflow_history.id},
    )
    response = api_client.post(url, **get_api_kwargs(token))

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "error": "ERROR_AUTOMATION_WORKFLOW_HISTORY_CANCELLATION_ALREADY_REQUESTED",
        "detail": (
            "The cancellation of the automation workflow history was already requested."
        ),
    }

    workflow_history.refresh_from_db()
    assert workflow_history.status == HistoryStatusChoices.STARTED
    assert workflow_history.cancellation_requested_by == requester
    assert workflow_history.cancellation_requested_on == requested_on
