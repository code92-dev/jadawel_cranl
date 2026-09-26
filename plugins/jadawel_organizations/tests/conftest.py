import pytest

from jadawel.test_utils.pytest_conftest import *  # noqa: F401,F403


@pytest.fixture(autouse=True)
def organization_settings(settings):
    settings.JADAWEL_BILLING_MODE = "test"
