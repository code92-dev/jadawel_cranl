"""
Every automation event and step the backend offers is in the editor's
catalogue and used by a recipe (docs/AUTOMATION_REDESIGN.md). A node type
added upstream, or by the fork, fails here until the editor describes it.
"""

import re
from pathlib import Path

import pytest

from jadawel.contrib.automation.nodes.registries import automation_node_type_registry

FRONTEND = Path(__file__).resolve().parents[3] / "web-frontend/modules/arabase"
CATALOG = FRONTEND / "automation/stepCatalog.js"
RECIPES = FRONTEND / "automation/recipes.js"


def read(path):
    if not path.exists():
        pytest.skip("web-frontend is not part of this checkout")
    return path.read_text()


def registered_types():
    return set(automation_node_type_registry.get_types())


def test_the_backend_offers_the_events_and_steps_the_editor_expects():
    types = registered_types()

    # Five events, Slack among the steps.
    assert {
        "local_jadawel_rows_created",
        "local_jadawel_rows_updated",
        "local_jadawel_rows_deleted",
        "periodic",
        "http_trigger",
        "slack_write_message",
    } <= types


def test_every_backend_step_is_in_the_editors_catalogue():
    block = read(CATALOG).split("export const STEP_CATALOG = {")[1].split("\n}\n")[0]
    catalogued = set(re.findall(r"^  ([a-z_]+): \{", block, re.MULTILINE))

    assert registered_types() - catalogued == set()


def test_every_backend_step_is_used_by_a_recipe():
    used = set(
        re.findall(r"'([a-z_]+)'", read(RECIPES).split("export const RECIPES")[1])
    )

    assert registered_types() - used == set()
