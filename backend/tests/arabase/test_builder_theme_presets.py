"""Theme presets for application-builder apps (docs/APPLICATION_REDESIGN.md)."""

import json
import runpy
from pathlib import Path

from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from arabase.builder.theme_presets import (
    ALIGNMENT_KEYS,
    PALETTES,
    as_json,
    language_values,
    preset_theme,
    preset_values,
)
from arabase.sanad.tools import SanadEndpoint, get_sanad_tools
from jadawel.contrib.builder.api.theme.serializers import (
    CombinedThemeConfigBlocksRequestSerializer,
    serialize_builder_theme,
)
from jadawel.contrib.builder.models import Builder
from jadawel.core.handler import CoreHandler

FRONTEND_COPY = (
    Path(__file__).resolve().parents[3]
    / "web-frontend/modules/arabase/builder/themePresets.json"
)


def contrast(first: str, second: str) -> float:
    def luminance(color):
        channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = [
            c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            for c in channels
        ]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    lighter, darker = sorted([luminance(first), luminance(second)], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("key", list(PALETTES))
def test_every_preset_value_is_a_valid_theme_property(key):
    values = preset_theme(key, "ar")
    serializer = CombinedThemeConfigBlocksRequestSerializer(data=values, partial=True)

    assert set(values) <= set(serializer.fields)
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize("key", list(PALETTES))
def test_every_preset_is_legible(key):
    p = PALETTES[key]

    assert contrast(p["primary"], p["on_primary"]) >= 4.5  # button labels
    assert contrast(p["primary_hover"], p["on_primary"]) >= 4.5
    assert contrast(p["primary"], p["surface"]) >= 4.5  # links
    assert contrast(p["text"], p["page"]) >= 7
    assert contrast(p["muted"], p["surface"]) >= 4.5
    assert contrast(p["header_text"], p["subtle"]) >= 4.5
    assert contrast(p["error"], p["surface"]) >= 4.5


def test_presets_leave_alignment_to_the_language():
    assert not set(ALIGNMENT_KEYS) & set(preset_values("jadawel"))
    assert "page_direction" not in preset_values("jadawel")

    arabic = language_values("ar")
    english = language_values("en-GB")

    assert {arabic[key] for key in ALIGNMENT_KEYS} == {"right"}
    assert arabic["page_direction"] == "rtl"
    assert {english[key] for key in ALIGNMENT_KEYS} == {"left"}
    assert english["page_direction"] == "ltr"
    # Button labels stay centred in their button either way.
    assert preset_values("jadawel")["button_text_alignment"] == "center"


def test_the_frontend_copy_matches():
    if not FRONTEND_COPY.exists():
        pytest.skip("web-frontend is not part of this checkout")

    assert json.loads(FRONTEND_COPY.read_text()) == as_json(), (
        "Regenerate it: PYTHONPATH=src python -m arabase.builder.theme_presets "
        "> ../web-frontend/modules/arabase/builder/themePresets.json"
    )


def theme_of(builder):
    return serialize_builder_theme(Builder.objects.get(pk=builder.pk))


@pytest.mark.django_db
def test_a_new_app_starts_from_the_jadawel_preset_in_its_creators_language(
    data_fixture,
):
    arabic = data_fixture.create_user()
    arabic.profile.language = "ar"
    arabic.profile.save()
    english = data_fixture.create_user()
    english.profile.language = "en"
    english.profile.save()
    workspace = data_fixture.create_workspace(users=[arabic, english])

    for user, side, direction in ((arabic, "right", "rtl"), (english, "left", "ltr")):
        builder = CoreHandler().create_application(
            user, workspace, "builder", name="App"
        )
        theme = theme_of(builder)

        assert theme["primary_color"] == preset_values("jadawel")["primary_color"]
        assert theme["button_border_radius"] == 8
        assert theme["table_vertical_separator_size"] == 0
        assert theme["heading_1_text_alignment"] == side
        assert theme["page_direction"] == direction


@pytest.mark.django_db
def test_the_creation_response_carries_the_new_theme(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)

    response = api_client.post(
        reverse("api:applications:list", kwargs={"workspace_id": workspace.id}),
        {"name": "App", "type": "builder"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    theme = response.json()["theme"]
    assert theme["primary_color"] == preset_values("jadawel")["primary_color"]
    assert theme["page_background_color"] == "#f7f9f6ff"


@pytest.mark.django_db
def test_a_duplicate_keeps_the_theme_it_was_made_with(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = CoreHandler().create_application(user, workspace, "builder", name="A")
    builder.colorthemeconfigblock.primary_color = "#aa0000ff"
    builder.colorthemeconfigblock.save()

    duplicate = CoreHandler().duplicate_application(user, builder)

    assert theme_of(duplicate)["primary_color"] == "#aa0000ff"


@pytest.mark.django_db
def test_the_page_direction_is_validated(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder = data_fixture.create_builder_application(user=user)
    url = reverse(
        "api:builder:builder_id:theme:update", kwargs={"builder_id": builder.id}
    )

    response = api_client.patch(
        url,
        {"page_direction": "sideways"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    response = api_client.patch(
        url,
        {"page_direction": "ltr"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert theme_of(builder)["page_direction"] == "ltr"


@pytest.mark.django_db
def test_sanad_applies_a_preset_for_a_language(data_fixture):
    user = data_fixture.create_user(is_staff=True)
    workspace = data_fixture.create_workspace(user=user)
    endpoint = SanadEndpoint(user=user, workspace=workspace)
    tool = next(t for t in get_sanad_tools() if t.name == "update_app_theme")
    builder = data_fixture.create_builder_application(workspace=workspace)

    result = tool.call(
        endpoint,
        {
            "application_id": builder.id,
            "preset": "heritage",
            "content_language": "en",
            "settings": {"heading_1_font_size": 36},
        },
    )

    theme = theme_of(builder)
    assert result["preset"] == "heritage"
    assert theme["primary_color"] == "#006c35ff"
    assert theme["heading_1_font_size"] == 36  # settings win over the preset
    assert theme["body_text_alignment"] == "left"
    assert theme["page_direction"] == "ltr"

    with pytest.raises(ValueError, match="Give a preset"):
        tool.call(endpoint, {"application_id": builder.id})


def test_the_module_prints_its_json(capsys):
    runpy.run_module("arabase.builder.theme_presets", run_name="__main__")

    assert json.loads(capsys.readouterr().out) == as_json()


def test_sanad_knows_every_preset():
    from arabase.sanad.skills import get_skills
    from arabase.sanad.tools.builder_elements import UpdateAppThemeInput

    schema = UpdateAppThemeInput.model_json_schema()["properties"]["preset"]
    offered = next(option["enum"] for option in schema["anyOf"] if "enum" in option)
    skill = get_skills()["app-builder"].instructions

    assert offered == list(PALETTES)
    for key in PALETTES:
        assert f"`{key}`" in skill
