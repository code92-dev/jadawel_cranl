"""
Box styles for application-builder elements: plain, card, tinted, outlined.

The Style panel offers them in one click
(`web-frontend/modules/arabase/builder/elementQuickStyles.js`) and marks the one
an element still matches; Sanad applies the same values through
`add_page_element(box_style=…)`, so its cards are the editor's cards. Both sides
compute them from the app's theme the same way; `test_builder_box_styles.py`
and `elementQuickStyles.spec.js` pin the same values.
"""

import re

BOX_STYLES = ("plain", "card", "tinted", "outlined")

SIDES = ("top", "bottom", "left", "right")

HEX = re.compile(r"^#?([0-9a-f]{6})([0-9a-f]{2})?$", re.IGNORECASE)


def _channels(color) -> list[int] | None:
    match = HEX.match(str(color or ""))
    if not match:
        return None
    value = match.group(1)
    return [int(value[i : i + 2], 16) for i in (0, 2, 4)]


def mix(color, base: str, amount: float) -> str:
    """`color` mixed into `base` by `amount` (0–1), as #rrggbbff."""

    a, b = _channels(color), _channels(base)
    if not a or not b:
        return base
    # Rounded half up, as JavaScript's Math.round does.
    mixed = [int(x * amount + y * (1 - amount) + 0.5) for x, y in zip(a, b)]
    return "#" + "".join(f"{channel:02x}" for channel in mixed) + "ff"


def surface_of(theme: dict) -> str:
    """The colour cards are drawn in: the theme's table cells, else white."""

    color = (theme or {}).get("table_cell_background_color")
    return color.lower() if _channels(color) else "#ffffffff"


def _sides(name: str, value) -> dict:
    return {f"style_border_{side}_{name}": value for side in SIDES}


def _padding(block: int, inline: int) -> dict:
    return {
        "style_padding_top": block,
        "style_padding_bottom": block,
        "style_padding_left": inline,
        "style_padding_right": inline,
    }


def box_style(key: str, theme: dict | None = None) -> dict:
    """
    The `style_*` values of the box style `key` in an app with `theme`.
    Raises `KeyError` for an unknown style.
    """

    theme = theme or {}
    surface = surface_of(theme)
    no_border = _sides("size", 0)
    line = {**_sides("size", 1), **_sides("color", "border")}
    styles = {
        "plain": {
            "style_background": "none",
            "style_background_radius": 0,
            "style_border_radius": 0,
            **no_border,
            **_padding(10, 20),
        },
        "card": {
            "style_background": "color",
            "style_background_color": surface,
            "style_background_radius": 12,
            "style_border_radius": 12,
            **line,
            **_padding(24, 24),
        },
        "tinted": {
            "style_background": "color",
            "style_background_color": mix(theme.get("primary_color"), surface, 0.08),
            "style_background_radius": 12,
            "style_border_radius": 12,
            **no_border,
            **_padding(24, 24),
        },
        "outlined": {
            "style_background": "none",
            "style_background_radius": 12,
            "style_border_radius": 12,
            **line,
            **_padding(20, 20),
        },
    }
    return styles[key]
