"""Sanad writing Page views (صفحة) through the ``html-pages`` skill.

Covers the tools in ``arabase/sanad/page_view_tools.py``: the data a model is
shown before it writes (shaped exactly like ``row.values`` in the page), the
write path (revisions, the REST artifact boundary), the checks that catch a
page which would render blank, and that the skill's own starter document
passes those checks.
"""

import re
from pathlib import Path

import pytest

from arabase.sanad.page_view_tools import SKILL, check_page_html
from arabase.sanad.skills import get_skills
from arabase.sanad.tools import SanadEndpoint, get_sanad_tools
from arabase.views.models import HtmlPageView, HtmlPageViewRevision
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.rows.handler import RowHandler

GOOD_PAGE = """<!doctype html><html dir="rtl"><head><style>
.card { margin-inline-start: 8px; text-align: start; }
</style></head><body><main id="app"></main><script>
window.jadawel.onData(({ rows }) => {
  document.getElementById('app').textContent = rows
    .map((r) => r.values['Name'] + ' ' + r.values['Amount']).join(', ')
})
</script></body></html>"""


def run(tool_name, endpoint, **arguments):
    tool = next(tool for tool in get_sanad_tools() if tool.name == tool_name)
    return tool.call(endpoint, arguments)


@pytest.fixture
def team(data_fixture):
    user = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    projects = data_fixture.create_database_table(database=database, name="Projects")
    project_name = data_fixture.create_text_field(
        table=projects, name="Project", primary=True
    )
    table = data_fixture.create_database_table(database=database, name="Team")
    name = data_fixture.create_text_field(table=table, name="Name", primary=True)
    amount = data_fixture.create_number_field(
        table=table, name="Amount", number_decimal_places=2
    )
    department = data_fixture.create_single_select_field(table=table, name="Department")
    sales = data_fixture.create_select_option(
        field=department, value="Sales", color="light-green"
    )
    link = data_fixture.create_link_row_field(
        table=table, link_row_table=projects, name="Projects"
    )
    (apollo,) = (
        RowHandler()
        .create_rows(user, projects, [{f"field_{project_name.id}": "Apollo"}])
        .created_rows
    )
    RowHandler().create_rows(
        user,
        table,
        [
            {
                f"field_{name.id}": "Sara",
                f"field_{amount.id}": "1250.50",
                f"field_{department.id}": sales.id,
                f"field_{link.id}": [apollo.id],
            },
            {f"field_{name.id}": "Omar"},
        ],
    )
    return {
        "user": user,
        "workspace": workspace,
        "database": database,
        "table": table,
        "endpoint": SanadEndpoint(user=user, workspace=workspace),
    }


def test_page_view_tools_belong_to_the_skill():
    tools = {tool.name: tool for tool in get_sanad_tools()}
    names = {
        "create_page_view",
        "get_page_view",
        "write_page_view",
        "edit_page_view",
        "list_page_view_revisions",
        "restore_page_view_revision",
    }

    assert {name: tools[name].skill for name in names} == dict.fromkeys(names, SKILL)
    assert SKILL in get_skills()


@pytest.mark.django_db
def test_a_new_page_shows_the_data_as_the_page_receives_it(team):
    page = run(
        "create_page_view", team["endpoint"], table_id=team["table"].id, name="Team"
    )

    view = HtmlPageView.objects.get(id=page["view_id"])
    assert view.table_id == team["table"].id and view.html == ""
    assert page["database_id"] == team["database"].id
    assert [field["name"] for field in page["fields"]] == [
        "Name",
        "Amount",
        "Department",
        "Projects",
    ]
    department = next(f for f in page["fields"] if f["name"] == "Department")
    assert department["options"] == [{"value": "Sales", "color": "light-green"}]
    assert page["row_count"] == 2 and page["truncated"] is False
    sara = page["row_sample"][0]
    # The shapes the skill's data table promises.
    assert sara["Amount"] == "1250.50"
    assert sara["Department"]["value"] == "Sales"
    assert sara["Department"]["color"] == "light-green"
    assert [item["value"] for item in sara["Projects"]] == ["Apollo"]
    assert page["row_sample"][1]["Amount"] is None
    assert "html" not in page


@pytest.mark.django_db
def test_writing_keeps_the_previous_document_and_checks_the_new_one(team):
    endpoint = team["endpoint"]
    view_id = run("create_page_view", endpoint, table_id=team["table"].id, name="P")[
        "view_id"
    ]

    first = run("write_page_view", endpoint, view_id=view_id, html=GOOD_PAGE)
    assert first["status"] == "saved" and first["warnings"] == []
    # Nothing to keep yet: the page was empty.
    assert not HtmlPageViewRevision.objects.filter(html_page_view_id=view_id).exists()

    bad = GOOD_PAGE.replace("values['Amount']", "values['Salary']").replace(
        "margin-inline-start", "margin-left"
    )
    bad = bad.replace(
        "</script>",
        "fetch('/api/'); localStorage.x = 1;"
        "(1).toLocaleString('ar-SA')</script>"
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
    )
    second = run("write_page_view", endpoint, view_id=view_id, html=bad, name="Q")
    warnings = " ".join(second["warnings"])
    assert "'Salary'" in warnings and "Amount" in warnings
    assert "fetch" in warnings
    assert "localStorage" in warnings
    assert "External files" in warnings
    assert "left/right" in warnings
    assert "Western digits" in warnings
    assert second["name"] == "Q"
    revisions = run("list_page_view_revisions", endpoint, view_id=view_id)
    assert len(revisions) == 1

    restored = run(
        "restore_page_view_revision",
        endpoint,
        view_id=view_id,
        revision_id=revisions[0]["revision_id"],
    )
    assert restored["warnings"] == []
    assert HtmlPageView.objects.get(id=view_id).html == GOOD_PAGE
    assert len(run("list_page_view_revisions", endpoint, view_id=view_id)) == 2

    page = run("get_page_view", endpoint, view_id=view_id)
    assert page["html"] == GOOD_PAGE


@pytest.mark.django_db
def test_edits_need_text_that_occurs_exactly_once(team):
    endpoint = team["endpoint"]
    view_id = run("create_page_view", endpoint, table_id=team["table"].id, name="P")[
        "view_id"
    ]
    run("write_page_view", endpoint, view_id=view_id, html=GOOD_PAGE)

    with pytest.raises(ValueError, match="occurs 0 times"):
        run(
            "edit_page_view",
            endpoint,
            view_id=view_id,
            edits=[{"find": "#123456", "replace": "#654321"}],
        )
    with pytest.raises(ValueError, match="occurs 2 times"):
        run(
            "edit_page_view",
            endpoint,
            view_id=view_id,
            edits=[{"find": "values[", "replace": "row.values["}],
        )

    result = run(
        "edit_page_view",
        endpoint,
        view_id=view_id,
        edits=[
            {"find": "text-align: start;", "replace": "text-align: end;"},
            {"find": "text-align: end;", "replace": "text-align: center;"},
        ],
    )
    assert result["status"] == "saved"
    assert "text-align: center;" in HtmlPageView.objects.get(id=view_id).html


@pytest.mark.django_db
def test_a_protected_page_is_left_to_its_approval_boundary(team, monkeypatch):
    endpoint = team["endpoint"]
    view_id = run("create_page_view", endpoint, table_id=team["table"].id, name="P")[
        "view_id"
    ]
    seen = {}

    def pending(self, values, view, user):
        seen.update(values=values, user=user)
        return {"status": "pending"}

    monkeypatch.setattr(HtmlPageViewType, "handle_view_update", pending)

    result = run("write_page_view", endpoint, view_id=view_id, html=GOOD_PAGE)

    assert result["status"] == "awaiting_approval"
    assert seen == {"values": {"html": GOOD_PAGE}, "user": team["user"]}
    assert HtmlPageView.objects.get(id=view_id).html == ""


@pytest.mark.django_db
def test_pages_stay_in_the_chat_workspace(team, data_fixture):
    other_user = data_fixture.create_user(is_staff=True)
    other_workspace = data_fixture.create_workspace(user=other_user)
    database = data_fixture.create_database_application(workspace=other_workspace)
    table = data_fixture.create_database_table(database=database)
    endpoint = SanadEndpoint(user=other_user, workspace=other_workspace)
    view_id = run("create_page_view", endpoint, table_id=table.id, name="Theirs")[
        "view_id"
    ]
    # The same user, but a chat in another of their workspaces.
    data_fixture.create_user_workspace(workspace=team["workspace"], user=other_user)
    elsewhere = SanadEndpoint(user=other_user, workspace=team["workspace"])

    for tool, extra in [
        ("get_page_view", {}),
        ("write_page_view", {"html": GOOD_PAGE}),
    ]:
        with pytest.raises(Exception, match="not in this endpoint's workspace"):
            run(tool, elsewhere, view_id=view_id, **extra)
    with pytest.raises(Exception, match="does not exist or is not accessible"):
        run("get_page_view", team["endpoint"], view_id=view_id)


def test_the_skills_starter_document_passes_the_checks():
    text = get_skills()["html-pages"].instructions
    starter = re.search(r"```html\n(.*?)```", text, re.S).group(1)

    assert check_page_html(starter, {"Name"}, allow_external=False) == []


def test_the_skill_names_only_the_runtime_the_page_really_has():
    root = Path(__file__).resolve().parents[3]
    runtime = (
        root / "web-frontend/modules/arabase/views/utils/pageDocument.js"
    ).read_text()
    api = set(re.findall(r"^\s{4}(\w+): (?:\[|null|function)", runtime, re.M))
    text = get_skills()["html-pages"].instructions

    assert api >= {"onData", "setHeight", "fields", "rows", "view"}
    assert set(re.findall(r"window\.jadawel\.(\w+)", text)) <= api
    # The view object the skill lists is the one HtmlPageView.vue sends.
    component = (
        root / "web-frontend/modules/arabase/views/components/HtmlPageView.vue"
    ).read_text()
    for key in ("id", "name", "count", "rowLimit", "truncated", "locale", "dir"):
        assert re.search(rf"^\s+{key}[:,]", component, re.M), key
