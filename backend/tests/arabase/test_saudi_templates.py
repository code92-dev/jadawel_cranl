import json
import re
from pathlib import Path

from django.core.files.storage import FileSystemStorage

import pytest

from arabase.template_catalog import LOCAL_TEMPLATE_CATALOG, SAUDI_EDITIONS
from jadawel.contrib.automation.nodes.models import AutomationNode
from jadawel.contrib.automation.workflows.models import AutomationWorkflow
from jadawel.contrib.builder.pages.models import Page
from jadawel.contrib.database.fields.models import Field, FormulaField
from jadawel.contrib.database.models import Database
from jadawel.contrib.database.table.models import Table
from jadawel.core.handler import CoreHandler
from jadawel.core.models import Template

TEMPLATES_DIR = Path(__file__).parents[2] / "templates"

# Saudi editions of upstream templates, built by tools/saudi_templates.
SAUDI_TEMPLATES = sorted([*SAUDI_EDITIONS, *(f"{slug}-en" for slug in SAUDI_EDITIONS)])


def test_every_saudi_edition_is_bundled_and_in_the_catalog():
    assert len(SAUDI_EDITIONS) == 15
    for slug in SAUDI_TEMPLATES:
        assert (TEMPLATES_DIR / f"{slug}.json").exists()
        assert slug in LOCAL_TEMPLATE_CATALOG


@pytest.mark.parametrize("slug", SAUDI_TEMPLATES)
def test_saudi_template_metadata(slug):
    payload = json.loads((TEMPLATES_DIR / f"{slug}.json").read_text())
    if slug.endswith("-en"):
        assert payload["categories"][0] == "English Templates"
    else:
        assert payload["categories"][:2] == ["قوالب عربية", "Arabic templates"]
        tables = [
            table
            for app in payload["export"]
            if app["type"] == "database"
            for table in app["tables"]
        ]
        assert all(any("؀" <= c <= "ۿ" for c in table["name"]) for table in tables)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("slug", SAUDI_TEMPLATES)
def test_saudi_template_installs_without_formula_errors(slug, data_fixture, tmpdir):
    payload = json.loads((TEMPLATES_DIR / f"{slug}.json").read_text())
    handler = CoreHandler()
    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler.sync_templates(storage=storage, pattern=f"^{slug}$", force=True)
    template = Template.objects.get(slug=slug)

    user = data_fixture.create_user()
    workspace = data_fixture.create_user_workspace(user=user).workspace
    applications, _ = handler.install_template(
        user, workspace, template, storage=storage
    )

    assert len(applications) == len(payload["export"])
    database = Database.objects.get(workspace=workspace)
    expected_tables = [
        table["name"]
        for app in payload["export"]
        if app["type"] == "database"
        for table in app["tables"]
    ]
    assert sorted(
        Table.objects.filter(database=database).values_list("name", flat=True)
    ) == sorted(expected_tables)
    broken = {
        f"{field.table.name}.{field.name}": field.error
        for field in FormulaField.objects.filter(table__database=database)
        if field.error
    }
    assert broken == {}

    workflows = [
        workflow
        for app in payload["export"]
        if app["type"] == "automation"
        for workflow in app["workflows"]
    ]
    installed_nodes = AutomationNode.objects.filter(
        workflow__automation__workspace=workspace
    )
    assert AutomationWorkflow.objects.filter(
        automation__workspace=workspace
    ).count() == len(workflows)
    assert installed_nodes.count() == sum(len(w["nodes"]) for w in workflows)
    assert not any(
        node.get_type().type == "slack_write_message" for node in installed_nodes
    )
    # Every field a step reads or writes was remapped to an installed field.
    field_ids = set(
        Field.objects.filter(table__database=database).values_list("id", flat=True)
    )
    for node in installed_nodes:
        service = node.service.specific
        exported = json.dumps(service.get_type().export_serialized(service))
        referenced = {int(i) for i in re.findall(r"field_(\d+)", exported)}
        referenced |= {int(i) for i in re.findall(r'"field_id": (\d+)', exported)}
        assert referenced <= field_ids, (node.label, referenced - field_ids)
    pages = [
        page
        for app in payload["export"]
        if app["type"] == "builder"
        for page in app["pages"]
    ]
    assert Page.objects.filter(builder__workspace=workspace).count() >= len(pages)
