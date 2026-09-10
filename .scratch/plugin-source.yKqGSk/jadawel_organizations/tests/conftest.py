import os
import sys

import pytest

from jadawel.test_utils.pytest_conftest import *  # noqa: F401,F403


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def organization_settings(settings):
    settings.JADAWEL_PLUGIN_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    settings.JADAWEL_BILLING_MODE = "test"
