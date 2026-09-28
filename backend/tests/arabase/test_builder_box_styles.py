"""Box styles: the editor's Style panel and Sanad draw the same boxes."""

import pytest

from arabase.builder.box_styles import BOX_STYLES, box_style, mix, surface_of
from arabase.builder.theme_presets import preset_theme
from arabase.sanad.tools import SanadEndpoint, get_sanad_tools

JADAWEL = preset_theme("jadawel", "ar")

# The same values `elementQuickStyles.spec.js` pins for the frontend.
CARD = {
    "style_background": "color",
    "style_background_color": "#ffffffff",
    "style_background_radius": 12,
    "style_border_radius": 12,
    "style_border_top_size": 1,
    "style_border_bottom_size": 1,
    "style_border_left_size": 1,
    "style_border_right_size": 1,
    "style_border_top_color": "border",
    "style_border_bottom_color": "border",
    "style_border_left_color": "border",
    "style_border_right_color": "border",
    "style_padding_top": 24,
    "style_padding_bottom": 24,
    "style_padding_left": 24,
    "style_padding_right": 24,
}


def test_box_styles_are_computed_from_the_theme():
    assert box_style("card", JADAWEL) == CARD
    assert box_style("tinted", JADAWEL)["style_background_color"] == "#eef5f1ff"
    assert box_style("tinted", JADAWEL)["style_border_top_size"] == 0
    assert box_style("outlined", JADAWEL)["style_background"] == "none"
    assert box_style("plain", JADAWEL)["style_padding_left"] == 20
    assert (
        box_style("card", {"table_cell_background_color": "#FAF8F2FF"})[
            "style_background_color"
        ]
        == "#faf8f2ff"
    )
    with pytest.raises(KeyError):
        box_style("glow", JADAWEL)


def test_mixing_rounds_like_the_frontend():
    assert mix("#278053ff", "#ffffffff", 0.08) == "#eef5f1ff"
    assert mix("primary", "#ffffffff", 0.5) == "#ffffffff"
    assert surface_of({}) == "#ffffffff"


def run(endpoint, tool_name, **arguments):
    tool = next(tool for tool in get_sanad_tools() if tool.name == tool_name)
    return tool.call(endpoint, arguments)


@pytest.mark.django_db
def test_sanad_draws_the_editors_boxes(data_fixture):
    from jadawel.contrib.builder.elements.models import Element

    user = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    endpoint = SanadEndpoint(user=user, workspace=workspace)
    app = run(endpoint, "create_builder_application", name="Catalogue")
    page = run(
        endpoint,
        "create_page",
        application_id=app["application_id"],
        name="Home",
        path="/",
    )

    card = run(
        endpoint,
        "add_page_element",
        page_id=page["page_id"],
        type="simple_container",
        box_style="card",
        settings={"style_padding_top": 32},
    )
    element = Element.objects.get(pk=card["id"])
    assert element.style_background_color == "#ffffffff"
    assert element.style_border_left_size == 1
    assert element.style_border_radius == 12
    assert element.style_padding_top == 32  # settings win over the box style
    assert element.style_padding_bottom == 24

    run(endpoint, "update_page_element", element_id=card["id"], box_style="tinted")
    element.refresh_from_db()
    assert element.style_background_color == "#eef5f1ff"
    assert element.style_border_left_size == 0

    with pytest.raises(ValueError, match="box_style"):
        run(endpoint, "update_page_element", element_id=card["id"])


def test_sanad_and_its_skill_offer_every_box_style():
    from arabase.sanad.skills import get_skills
    from arabase.sanad.tools.builder_elements import (
        AddPageElementInput,
        UpdatePageElementInput,
    )

    skill = get_skills()["app-builder"].instructions
    for model in (AddPageElementInput, UpdatePageElementInput):
        schema = model.model_json_schema()["properties"]["box_style"]
        offered = next(o["enum"] for o in schema["anyOf"] if "enum" in o)
        assert offered == list(BOX_STYLES)
    for key in BOX_STYLES:
        assert f"`{key}`" in skill
