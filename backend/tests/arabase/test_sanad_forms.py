"""Sanad building Form views (نموذج) through the ``forms`` skill.

Covers ``arabase/sanad/tools/form.py``: a form arrives asking its questions in
one call (``create_view`` alone leaves every field disabled), fields a form
cannot fill are refused or reported, conditions and select values are stored
the way the form renders them, and the public link waits for approval.
"""

from django.conf import settings

import pytest

from arabase.sanad.skills import get_skills
from arabase.sanad.tools import APPROVAL_TOOLS, SanadEndpoint, get_sanad_tools
from arabase.sanad.tools.form import SKILL
from jadawel.contrib.database.views.models import FormView, FormViewFieldOptions


def run(tool_name, endpoint, **arguments):
    tool = next(tool for tool in get_sanad_tools() if tool.name == tool_name)
    return tool.call(endpoint, arguments)


@pytest.fixture
def leads(data_fixture):
    user = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database, name="Leads")
    fields = {
        "name": data_fixture.create_text_field(table=table, name="Name", primary=True),
        "email": data_fixture.create_email_field(table=table, name="Email"),
        "source": data_fixture.create_single_select_field(table=table, name="Source"),
        "other": data_fixture.create_text_field(table=table, name="Other source"),
        "budget": data_fixture.create_number_field(table=table, name="Budget"),
        "score": data_fixture.create_formula_field(
            table=table, name="Score", formula="1"
        ),
    }
    options = {
        "web": data_fixture.create_select_option(field=fields["source"], value="Web"),
        "other": data_fixture.create_select_option(
            field=fields["source"], value="Other"
        ),
    }
    return {
        "endpoint": SanadEndpoint(user=user, workspace=workspace),
        "table": table,
        "fields": fields,
        "options": options,
    }


def options_by_field(view_id):
    return {
        option.field_id: option
        for option in FormViewFieldOptions.objects.filter(form_view_id=view_id)
    }


def test_form_tools_belong_to_the_skill_and_sharing_needs_approval():
    tools = {tool.name: tool for tool in get_sanad_tools()}
    names = {"create_form", "get_form", "update_form", "share_form"}

    assert {name: tools[name].skill for name in names} == dict.fromkeys(names, SKILL)
    assert SKILL in get_skills()
    assert "share_form" in APPROVAL_TOOLS
    assert not {"create_form", "get_form", "update_form"} & APPROVAL_TOOLS


@pytest.mark.django_db
def test_a_new_form_asks_every_field_it_can_fill(leads):
    form = run(
        "create_form",
        leads["endpoint"],
        table_id=leads["table"].id,
        name="Contact us",
        title="تواصل معنا",
        submit_text="أرسل",
        success_message="شكرًا لك!",
    )

    view = FormView.objects.get(id=form["view_id"])
    assert (view.title, view.submit_text) == ("تواصل معنا", "أرسل")
    assert view.submit_action == "MESSAGE"
    assert view.submit_action_message == "شكرًا لك!"
    assert [q["field_name"] for q in form["questions"]] == [
        "Name",
        "Email",
        "Source",
        "Other source",
        "Budget",
    ]
    # A formula cannot be filled in; it is reported rather than silently lost.
    assert form["skipped_fields"] == [
        {
            "field_id": leads["fields"]["score"].id,
            "name": "Score",
            "reason": "computed or read-only",
        }
    ]
    assert form["shared"] is False and form["public_url"] is None


@pytest.mark.django_db
def test_questions_set_order_labels_required_and_conditions(leads):
    fields, options = leads["fields"], leads["options"]
    form = run(
        "create_form",
        leads["endpoint"],
        table_id=leads["table"].id,
        name="Leads",
        questions=[
            {"field_id": fields["email"].id, "label": "بريدك", "required": True},
            {"field_id": fields["source"].id, "style": "radios"},
            {
                "field_id": fields["other"].id,
                "description": "أخبرنا كيف عرفتنا",
                # Written as the option's text; stored as its ID, the only
                # value a select condition matches.
                "show_when": [
                    {
                        "field_id": fields["source"].id,
                        "type": "single_select_equal",
                        "value": "other",
                    }
                ],
            },
        ],
    )

    stored = options_by_field(form["view_id"])
    email, source, other = (
        stored[fields["email"].id],
        stored[fields["source"].id],
        stored[fields["other"].id],
    )
    assert [email.order, source.order, other.order] == [0, 1, 2]
    assert (email.enabled, email.required, email.name) == (True, True, "بريدك")
    assert source.field_component == "radios"
    assert other.show_when_matching_conditions is True
    (condition,) = other.conditions.all()
    assert condition.field_id == fields["source"].id
    assert condition.value == str(options["other"].id)
    # Fields left out are not asked.
    assert stored[fields["name"].id].enabled is False
    assert stored[fields["budget"].id].enabled is False

    described = run("get_form", leads["endpoint"], view_id=form["view_id"])
    assert [q["label"] for q in described["questions"]] == [
        "بريدك",
        "Source",
        "Other source",
    ]
    assert described["questions"][2]["show_when"][0]["field_name"] == "Source"
    assert {f["name"] for f in described["not_asked"]} == {"Name", "Budget", "Score"}


@pytest.mark.django_db
def test_mistakes_are_refused_with_a_reason(leads):
    fields, endpoint, table_id = leads["fields"], leads["endpoint"], leads["table"].id

    def create(**arguments):
        return run("create_form", endpoint, table_id=table_id, name="F", **arguments)

    with pytest.raises(ValueError, match="'Score' cannot be a question"):
        create(questions=[{"field_id": fields["score"].id}])
    with pytest.raises(ValueError, match="no 'radios' style"):
        create(questions=[{"field_id": fields["budget"].id, "style": "radios"}])
    with pytest.raises(ValueError, match="earlier question"):
        create(
            questions=[
                {
                    "field_id": fields["other"].id,
                    "show_when": [
                        {"field_id": fields["source"].id, "type": "not_empty"}
                    ],
                },
                {"field_id": fields["source"].id},
            ]
        )
    with pytest.raises(ValueError, match="is not an option"):
        create(
            questions=[
                {"field_id": fields["source"].id},
                {
                    "field_id": fields["other"].id,
                    "show_when": [
                        {
                            "field_id": fields["source"].id,
                            "type": "single_select_equal",
                            "value": "Radio",
                        }
                    ],
                },
            ]
        )
    with pytest.raises(ValueError, match="Invalid form settings"):
        create(redirect_url="not a url")


@pytest.mark.django_db
def test_updating_replaces_the_questions_and_keeps_the_rest(leads):
    fields, endpoint = leads["fields"], leads["endpoint"]
    form = run(
        "create_form",
        endpoint,
        table_id=leads["table"].id,
        name="Leads",
        title="Old",
    )

    updated = run(
        "update_form",
        endpoint,
        view_id=form["view_id"],
        redirect_url="https://example.com/thanks",
        questions=[
            {"field_id": fields["budget"].id, "required": True},
            {"field_id": fields["name"].id},
        ],
    )

    assert updated["title"] == "Old"
    assert updated["after_submit"] == {"redirect_url": "https://example.com/thanks"}
    assert [q["field_name"] for q in updated["questions"]] == ["Budget", "Name"]

    retitled = run("update_form", endpoint, view_id=form["view_id"], title="New")
    assert retitled["title"] == "New"
    assert [q["field_name"] for q in retitled["questions"]] == ["Budget", "Name"]


@pytest.mark.django_db
def test_sharing_turns_on_the_public_link(leads):
    form = run(
        "create_form", leads["endpoint"], table_id=leads["table"].id, name="Leads"
    )

    shared = run("share_form", leads["endpoint"], view_id=form["view_id"])

    view = FormView.objects.get(id=form["view_id"])
    assert view.public is True
    assert shared["public_url"] == (
        f"{settings.PUBLIC_WEB_FRONTEND_URL}/form/{view.slug}"
    )


@pytest.mark.django_db
def test_forms_stay_in_the_chat_workspace(leads, data_fixture):
    other_table = data_fixture.create_database_table()
    foreign = data_fixture.create_form_view(table=other_table)
    grid = data_fixture.create_grid_view(table=leads["table"])

    with pytest.raises(Exception) as missing:
        run("get_form", leads["endpoint"], view_id=foreign.id)
    assert "DoesNotExist" in type(missing.value).__name__
    with pytest.raises(ValueError, match="not a form"):
        run("get_form", leads["endpoint"], view_id=grid.id)


@pytest.mark.django_db
def test_create_view_sends_forms_to_create_form(leads):
    with pytest.raises(ValueError, match="create_form"):
        run(
            "create_view",
            leads["endpoint"],
            table_id=leads["table"].id,
            name="Empty form",
            type="form",
        )


@pytest.mark.django_db
def test_a_conditional_required_answer_is_only_required_in_the_browser(leads):
    """What the skill warns about: the server cannot tell whether a
    conditional question was shown, so it accepts a submission without it."""

    from jadawel.contrib.database.views.handler import ViewHandler

    fields = leads["fields"]
    form = run(
        "create_form",
        leads["endpoint"],
        table_id=leads["table"].id,
        name="Leads",
        questions=[
            {"field_id": fields["name"].id, "required": True},
            {"field_id": fields["source"].id},
            {
                "field_id": fields["other"].id,
                "required": True,
                "show_when": [{"field_id": fields["source"].id, "type": "not_empty"}],
            },
        ],
    )
    view = FormView.objects.get(id=form["view_id"])
    name = f"field_{fields['name'].id}"

    row = ViewHandler().submit_form_view(leads["endpoint"].user, view, {name: "Sara"})
    assert getattr(row, name) == "Sara"
    with pytest.raises(Exception, match="required"):
        ViewHandler().submit_form_view(leads["endpoint"].user, view, {})
