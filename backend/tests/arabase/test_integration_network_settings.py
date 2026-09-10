"""An explicitly disabled private-network opt-in must keep SSRF checks enabled."""

import importlib

import pytest

import advocate
from jadawel.config.settings import base
from jadawel.contrib.integrations.utils import get_http_request_function

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", [None, "", "false", "False", "off", "0", "no"])
def test_private_address_false_values_keep_address_validation(
    monkeypatch, settings, value
):
    name = "JADAWEL_INTEGRATIONS_ALLOW_PRIVATE_ADDRESS"
    # Load the actual environment-backed setting, not a duplicate of its parser.
    with monkeypatch.context() as context:
        if value is None:
            context.delenv(name, raising=False)
        else:
            context.setenv(name, value)
        try:
            configured = importlib.reload(base).INTEGRATIONS_ALLOW_PRIVATE_ADDRESS
        finally:
            context.undo()
            importlib.reload(base)

    assert configured is False
    settings.INTEGRATIONS_ALLOW_PRIVATE_ADDRESS = configured
    assert get_http_request_function() is advocate.request


@pytest.mark.parametrize("value", ["true", "TRUE", "on", "1", "yes"])
def test_private_address_access_requires_explicit_opt_in(monkeypatch, value):
    with monkeypatch.context() as context:
        context.setenv("JADAWEL_INTEGRATIONS_ALLOW_PRIVATE_ADDRESS", value)
        try:
            configured = importlib.reload(base).INTEGRATIONS_ALLOW_PRIVATE_ADDRESS
        finally:
            context.undo()
            importlib.reload(base)

    assert configured is True
