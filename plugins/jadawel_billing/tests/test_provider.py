from unittest.mock import Mock, patch

import pytest
import requests
from jadawel_billing.errors import ProviderUnavailable


def test_moyasar_client_rejects_wrong_environment_key():
    from jadawel_billing.providers.moyasar import MoyasarClient

    with pytest.raises(ProviderUnavailable) as error:
        MoyasarClient(secret_key="sk_live_fixture", mode="test")
    assert error.value.default_code == "payment_verification_unavailable"


def test_moyasar_client_converts_timeout_to_retryable_error():
    from jadawel_billing.providers.moyasar import MoyasarClient

    with patch("requests.get", side_effect=requests.Timeout):
        with pytest.raises(ProviderUnavailable) as error:
            MoyasarClient(secret_key="sk_test_fixture", mode="test").fetch("payment-1")
    assert error.value.status_code == 503


def test_moyasar_client_only_returns_json_objects():
    from jadawel_billing.providers.moyasar import MoyasarClient

    response = Mock(status_code=200)
    response.json.return_value = ["not", "a", "payment"]
    with patch("requests.get", return_value=response):
        with pytest.raises(ProviderUnavailable) as error:
            MoyasarClient(secret_key="sk_test_fixture", mode="test").fetch("payment-1")
    assert error.value.status_code == 503


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (200, {"status": "ok", "reachable": True}),
        (401, {"status": "invalid_credentials", "reachable": True}),
    ],
)
def test_moyasar_client_health_returns_safe_status(status_code, expected):
    from jadawel_billing.providers.moyasar import MoyasarClient

    response = Mock(status_code=status_code)
    with patch("requests.get", return_value=response) as get:
        assert (
            MoyasarClient(secret_key="sk_test_fixture", mode="test").health()
            == expected
        )
    get.assert_called_once()


def test_moyasar_client_health_handles_unreachable_provider():
    from jadawel_billing.providers.moyasar import MoyasarClient

    with patch("requests.get", side_effect=requests.Timeout):
        assert MoyasarClient(secret_key="sk_test_fixture", mode="test").health() == {
            "status": "unreachable",
            "reachable": False,
        }
