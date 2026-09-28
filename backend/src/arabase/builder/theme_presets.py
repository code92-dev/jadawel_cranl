"""
Theme presets for application-builder apps.

A preset is a complete builder theme — colours, type scale, buttons, links,
inputs, tables, images and the page — drawn from the same system as the
redesigned dashboards: white surfaces on a quiet page, 8 px controls, 12 px
cards and tables, a type scale that steps clearly, one accent for actions.
docs/APPLICATION_REDESIGN.md explains the choices.

Alignment and direction are not part of a preset's look but of the language
its content is written in, so a preset is applied for a language: Arabic sets
every alignment to the right and the page to right-to-left, English to the
left and left-to-right.

This module is the source of truth. The frontend reads the same data from
`web-frontend/modules/arabase/builder/themePresets.json`, which is generated
from it:

    cd backend && PYTHONPATH=src python -m arabase.builder.theme_presets \
        > ../web-frontend/modules/arabase/builder/themePresets.json
    cd ../web-frontend && npx prettier --write modules/arabase/builder/themePresets.json

`test_builder_theme_presets.py` fails when the two drift.
"""

import json
import sys

DEFAULT_PRESET = "jadawel"
LANGUAGES = ("ar", "en")

# The palettes. `ink` is for headings, `text` for body copy, `muted` for the
# smallest heading and table headers' secondary tone, `subtle` a tint for table
# headers, `line` for separators, `field` for input borders. Every `primary`
# carries `on_primary` text at WCAG AA (4.5:1) or better; the tests check it.
# All are light: elements keep the colours they were given one by one (a white
# card is white on any theme), so a dark page would strand them.
PALETTES = {
    # The product's own sage, as on the dashboards.
    "jadawel": {
        "primary": "#278053",
        "primary_hover": "#216d46",
        "primary_active": "#1b5a3a",
        "on_primary": "#ffffff",
        "secondary": "#3c76c7",
        "border": "#d3dbcf",
        "success": "#1f8a4c",
        "warning": "#e8a317",
        "error": "#d93c2f",
        "page": "#f7f9f6",
        "surface": "#ffffff",
        "ink": "#080b07",
        "text": "#1e241d",
        "muted": "#667063",
        "subtle": "#f4f7f2",
        "line": "#eaefe7",
        "field": "#d3dbcf",
        "header_text": "#4d564b",
    },
    # The logo's blue, for apps that should read as Jadawel's brand.
    "ocean": {
        "primary": "#0059fc",
        "primary_hover": "#004ad4",
        "primary_active": "#003caa",
        "on_primary": "#ffffff",
        "secondary": "#278053",
        "border": "#d5dbe6",
        "success": "#1f8a4c",
        "warning": "#e8a317",
        "error": "#d93c2f",
        "page": "#f5f7fb",
        "surface": "#ffffff",
        "ink": "#0b1220",
        "text": "#1c2433",
        "muted": "#5b6475",
        "subtle": "#eef2f8",
        "line": "#e3e8f0",
        "field": "#cbd3df",
        "header_text": "#3d4657",
    },
    # Deep green and gold on warm paper: formal, for public services.
    "heritage": {
        "primary": "#006c35",
        "primary_hover": "#005a2c",
        "primary_active": "#004822",
        "on_primary": "#ffffff",
        "secondary": "#a8802c",
        "border": "#ddd6c6",
        "success": "#1f8a4c",
        "warning": "#d4940f",
        "error": "#c6392d",
        "page": "#f8f6f1",
        "surface": "#ffffff",
        "ink": "#14120d",
        "text": "#2a261d",
        "muted": "#6f6858",
        "subtle": "#f3efe6",
        "line": "#ebe5d8",
        "field": "#d6cfbe",
        "header_text": "#4f4839",
    },
    # Terracotta and teal on sand: warm, for community and hospitality apps.
    "sand": {
        "primary": "#a94f28",
        "primary_hover": "#8f4220",
        "primary_active": "#76361a",
        "on_primary": "#ffffff",
        "secondary": "#2f6f73",
        "border": "#dfd3c4",
        "success": "#1f8a4c",
        "warning": "#d4940f",
        "error": "#c6392d",
        "page": "#fbf8f4",
        "surface": "#ffffff",
        "ink": "#1f1712",
        "text": "#33291f",
        "muted": "#7a6a5b",
        "subtle": "#f6f0e8",
        "line": "#eee5da",
        "field": "#dccfbf",
        "header_text": "#5a4a3c",
    },
    # Steel navy on cool grey: sober, for finance and back-office apps.
    "stone": {
        "primary": "#2f4a6d",
        "primary_hover": "#263d5a",
        "primary_active": "#1e3048",
        "on_primary": "#ffffff",
        "secondary": "#278053",
        "border": "#d6dbe2",
        "success": "#1f8a4c",
        "warning": "#d4940f",
        "error": "#c6392d",
        "page": "#f6f7f9",
        "surface": "#ffffff",
        "ink": "#0e1116",
        "text": "#1f252d",
        "muted": "#5e6773",
        "subtle": "#f0f2f5",
        "line": "#e4e7ec",
        "field": "#cfd5dd",
        "header_text": "#3f4854",
    },
}

ALIGNMENT_KEYS = [
    "body_text_alignment",
    "heading_1_text_alignment",
    "heading_2_text_alignment",
    "heading_3_text_alignment",
    "heading_4_text_alignment",
    "heading_5_text_alignment",
    "heading_6_text_alignment",
    "button_alignment",
    "link_text_alignment",
    "image_alignment",
    "table_header_text_alignment",
    "table_cell_alignment",
]

# (size, weight) per heading level: steps a reader can tell apart at a glance.
HEADINGS = {
    1: (32, "bold"),
    2: (24, "semi-bold"),
    3: (19, "semi-bold"),
    4: (16, "semi-bold"),
    5: (14, "medium"),
    6: (13, "medium"),
}

FONT = "inter"
NO_DECORATION = [False, False, False, False]
UNDERLINE = [True, False, False, False]


def _hex(color: str) -> str:
    """The builder stores colours as #rrggbbaa."""

    return f"{color.lower()}ff"


def preset_values(key: str) -> dict:
    """
    The theme values of the preset `key`, without alignment and direction.
    Raises `KeyError` for an unknown preset.
    """

    p = PALETTES[key]
    c = {name: _hex(value) for name, value in p.items()}
    values = {
        # Colours
        "primary_color": c["primary"],
        "secondary_color": c["secondary"],
        "border_color": c["border"],
        "main_success_color": c["success"],
        "main_warning_color": c["warning"],
        "main_error_color": c["error"],
        # Page
        "page_background_color": c["page"],
        # Body text
        "body_font_family": FONT,
        "body_font_size": 15,
        "body_font_weight": "regular",
        "body_text_color": c["text"],
        # Buttons: 8 px corners, a comfortable target, the accent for actions.
        "button_font_family": FONT,
        "button_font_size": 14,
        "button_font_weight": "semi-bold",
        "button_text_alignment": "center",
        "button_width": "auto",
        "button_background_color": c["primary"],
        "button_text_color": c["on_primary"],
        "button_border_color": c["primary"],
        "button_border_size": 0,
        "button_border_radius": 8,
        "button_vertical_padding": 10,
        "button_horizontal_padding": 18,
        "button_hover_background_color": c["primary_hover"],
        "button_hover_text_color": c["on_primary"],
        "button_hover_border_color": c["primary_hover"],
        "button_active_background_color": c["primary_active"],
        "button_active_text_color": c["on_primary"],
        "button_active_border_color": c["primary_active"],
        # Links: the accent, underlined only when pointed at.
        "link_font_family": FONT,
        "link_font_size": 14,
        "link_font_weight": "medium",
        "link_text_color": c["primary"],
        "link_hover_text_color": c["primary_hover"],
        "link_active_text_color": c["primary_active"],
        "link_default_text_decoration": NO_DECORATION,
        "link_hover_text_decoration": UNDERLINE,
        "link_active_text_decoration": UNDERLINE,
        # Images: rounded like the cards around them.
        "image_max_width": 100,
        "image_border_radius": 12,
        "image_constraint": "contain",
        # Form labels and inputs
        "label_font_family": FONT,
        "label_font_size": 13,
        "label_font_weight": "medium",
        "label_text_color": c["text"],
        "input_font_family": FONT,
        "input_font_size": 14,
        "input_font_weight": "regular",
        "input_text_color": c["text"],
        "input_background_color": c["surface"],
        "input_border_color": c["field"],
        "input_border_size": 1,
        "input_border_radius": 8,
        "input_vertical_padding": 10,
        "input_horizontal_padding": 12,
        # Tables: a card with a quiet header and row lines, no grid.
        "table_border_color": c["line"],
        "table_border_size": 1,
        "table_border_radius": 12,
        "table_header_background_color": c["subtle"],
        "table_header_text_color": c["header_text"],
        "table_header_font_size": 13,
        "table_header_font_weight": "semi-bold",
        "table_header_font_family": FONT,
        "table_cell_background_color": c["surface"],
        "table_cell_alternate_background_color": c["surface"],
        "table_cell_vertical_padding": 12,
        "table_cell_horizontal_padding": 16,
        "table_vertical_separator_color": c["line"],
        "table_vertical_separator_size": 0,
        "table_horizontal_separator_color": c["line"],
        "table_horizontal_separator_size": 1,
    }
    for level, (size, weight) in HEADINGS.items():
        values[f"heading_{level}_font_family"] = FONT
        values[f"heading_{level}_font_size"] = size
        values[f"heading_{level}_font_weight"] = weight
        values[f"heading_{level}_text_color"] = c["muted"] if level == 6 else c["ink"]
        values[f"heading_{level}_text_decoration"] = NO_DECORATION
    return values


def language_values(language: str) -> dict:
    """
    Alignment and direction for content written in `language`: Arabic reads
    from the right, everything else from the left.
    """

    arabic = str(language or "").split("-")[0] == "ar"
    values = {key: "right" if arabic else "left" for key in ALIGNMENT_KEYS}
    values["page_direction"] = "rtl" if arabic else "ltr"
    return values


def preset_theme(key: str = DEFAULT_PRESET, language: str = "ar") -> dict:
    """The full theme update for the preset `key` in `language`."""

    return {**preset_values(key), **language_values(language)}


def swatches(key: str) -> dict:
    """The colours a preset card previews."""

    p = PALETTES[key]
    return {
        name: p[name]
        for name in ("primary", "on_primary", "secondary", "page", "surface", "ink")
    } | {"text": p["text"], "line": p["line"], "subtle": p["subtle"]}


def as_json() -> dict:
    """What the frontend reads: every preset's values and swatches."""

    return {
        "default": DEFAULT_PRESET,
        "presets": [
            {"key": key, "swatches": swatches(key), "values": preset_values(key)}
            for key in PALETTES
        ],
        "languages": {language: language_values(language) for language in LANGUAGES},
    }


if __name__ == "__main__":
    json.dump(as_json(), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
