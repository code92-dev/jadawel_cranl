import uuid
from types import SimpleNamespace
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from jadawel.contrib.automation.history.handler import AutomationHistoryHandler
from jadawel.contrib.automation.history.models import AutomationWorkflowHistory
from jadawel.contrib.automation.workflows.constants import WorkflowState
from jadawel.contrib.automation.workflows.handler import AutomationWorkflowHandler
from jadawel.contrib.integrations.core.api.webhooks.views import CoreHTTPTriggerView
from jadawel.contrib.integrations.core.constants import RESPONSE_BODY_TYPE
from jadawel.contrib.integrations.core.models import CoreResponseHeader
from jadawel.core.services.registries import service_type_registry


def get_url(uid):
    return reverse("api:http_trigger", kwargs={"webhook_uid": uid})


@pytest.mark.parametrize(
    "http_method",
    ["head", "options", "trace"],
)
@pytest.mark.django_db
def test_rejects_disallowed_methods(api_client, data_fixture, http_method):
    node = data_fixture.create_http_trigger_node()

    url = get_url(node.service.uid)
    resp = getattr(api_client, http_method)(url)

    assert resp.status_code == HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_rejects_http_get_if_service_excludes_get(
    api_client, data_fixture, django_assert_num_queries
):
    node = data_fixture.create_http_trigger_node()
    node.service.exclude_get = True
    node.service.save()

    url = get_url(node.service.uid) + "?test=true"

    with django_assert_num_queries(1):
        resp = api_client.get(url)

    assert resp.status_code == HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "http_method",
    ["get", "post", "put", "patch", "delete"],
)
def test_allows_valid_http_methods(api_client, data_fixture, http_method):
    node = data_fixture.create_http_trigger_node()

    url = get_url(node.service.uid) + "?test=true"
    resp = getattr(api_client, http_method)(url)

    assert resp.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db(transaction=True)
def test_http_trigger_with_response_node_returns_workflow_response(
    api_client, data_fixture
):
    trigger = data_fixture.create_http_trigger_node(
        service_kwargs={
            "wait_for_response": True,
            "response_timeout_seconds": 1,
        },
    )
    workflow = trigger.workflow
    workflow.state = WorkflowState.LIVE
    workflow.allow_test_run_until = timezone.now()
    workflow.save()
    response_node = data_fixture.create_core_response_action_node(
        workflow=workflow,
        service_kwargs={
            "status_code": HTTP_200_OK,
            "body_type": RESPONSE_BODY_TYPE.TEXT,
            "body": "'Hello'",
        },
    )
    CoreResponseHeader.objects.create(
        service=response_node.service.specific,
        key="X-Workflow",
        value="'done'",
    )
    url = get_url(trigger.service.uid) + "?test=true"
    resp = api_client.post(url)

    assert resp.status_code == HTTP_200_OK
    assert resp.content == b"Hello"
    assert resp["X-Workflow"] == "done"


@pytest.mark.parametrize(
    "content_type_header_key",
    ["Content-Type", "content-type", "CoNtEnT-TyPe"],
)
def test_text_workflow_response_content_type_is_case_insensitive(
    content_type_header_key,
):
    workflow_response = SimpleNamespace(
        headers={content_type_header_key: "text/custom", "X-Workflow": "done"},
        status_code=HTTP_200_OK,
        body_type=RESPONSE_BODY_TYPE.TEXT,
        body="Hello",
    )

    response = CoreHTTPTriggerView().response_to_http_response(workflow_response)

    assert response.status_code == HTTP_200_OK
    assert response.content == b"Hello"
    assert response["Content-Type"] == "text/custom"
    assert response["X-Workflow"] == "done"


@pytest.mark.parametrize(
    "csp_header_key",
    ["Content-Security-Policy", "content-security-policy", "CoNtEnT-SeCuRiTy-PoLiCy"],
)
def test_workflow_response_enforces_browser_sandbox(csp_header_key):
    workflow_response = SimpleNamespace(
        headers={
            "Content-Type": "text/html",
            csp_header_key: "script-src * 'unsafe-inline'",
        },
        status_code=HTTP_200_OK,
        body_type=RESPONSE_BODY_TYPE.TEXT,
        body="<script>alert('foo')</script>",
    )

    response = CoreHTTPTriggerView().response_to_http_response(workflow_response)

    assert response.content == b"<script>alert('foo')</script>"
    assert response["Content-Type"] == "text/html"
    assert response["Content-Security-Policy"] == "sandbox"


@pytest.mark.parametrize(
    "header_name",
    [
        "Set-Cookie",
        "clear-site-data",
        "StRiCt-TrAnSpOrT-SeCuRiTy",
    ],
)
def test_workflow_response_strips_shared_origin_state_headers(header_name):
    workflow_response = SimpleNamespace(
        headers={header_name: "unsafe", "X-Workflow": "done"},
        status_code=HTTP_200_OK,
        body_type=RESPONSE_BODY_TYPE.TEXT,
        body="Hello",
    )

    response = CoreHTTPTriggerView().response_to_http_response(workflow_response)

    assert not response.has_header(header_name)
    assert response["X-Workflow"] == "done"


@pytest.mark.django_db(transaction=True)
def test_http_trigger_does_not_wait_for_response_when_disabled(
    api_client, data_fixture
):
    trigger = data_fixture.create_http_trigger_node()
    workflow = trigger.workflow
    workflow.state = WorkflowState.LIVE
    workflow.allow_test_run_until = timezone.now()
    workflow.save()
    data_fixture.create_core_response_action_node(workflow=workflow)

    resp = api_client.post(get_url(trigger.service.uid) + "?test=true")

    assert resp.status_code == HTTP_204_NO_CONTENT


def test_http_trigger_does_not_wait_for_node_simulation(api_request_factory):
    """Node simulations delete their history, so the webhook must not poll it."""

    service = SimpleNamespace(
        wait_for_response=True,
        response_timeout_seconds=10,
    )
    history = SimpleNamespace(simulate_until_node_id=123)
    service_type = service_type_registry.get("http_trigger")
    request = api_request_factory.post("/?test=true")

    with (
        patch.object(
            service_type,
            "process_webhook_request",
            return_value=(service, history),
        ),
        patch.object(
            AutomationHistoryHandler, "wait_for_workflow_response"
        ) as mock_wait,
    ):
        response = CoreHTTPTriggerView.as_view()(request, webhook_uid=uuid.uuid4())

    assert response.status_code == HTTP_204_NO_CONTENT
    mock_wait.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_http_trigger_rolls_back_mutations_before_waiting(api_client, data_fixture):
    """A mutation failure rolls back history and discards deferred scheduling."""

    trigger = data_fixture.create_http_trigger_node(
        service_kwargs={"wait_for_response": True}
    )
    workflow = trigger.workflow
    workflow.state = WorkflowState.LIVE
    workflow.allow_test_run_until = timezone.now()
    workflow.save()

    with (
        patch.object(
            AutomationWorkflowHandler,
            "reset_workflow_temporary_states",
            side_effect=[None, RuntimeError("reset failed")],
        ),
        patch(
            "jadawel.contrib.automation.workflows.handler."
            "start_workflow_celery_task.delay"
        ) as mock_delay,
        pytest.raises(RuntimeError, match="reset failed"),
    ):
        api_client.post(get_url(trigger.service.uid) + "?test=true")

    assert AutomationWorkflowHistory.objects.count() == 0
    mock_delay.assert_not_called()
