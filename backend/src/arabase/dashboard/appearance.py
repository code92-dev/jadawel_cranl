"""The appearance options widgets understand, for Sanad to choose from.

The widget API stores `appearance` as a bounded flat dict and leaves its meaning
to the frontend (`web-frontend/modules/arabase/dashboard/appearance.js`), which
ignores values it does not know. These lists mirror that file so Sanad offers
only what renders; `web-frontend/test/unit/arabase/dashboard/appearance.spec.js`
keeps the two in step.
"""

ACCENT_COLORS = (
    "primary",
    "blue",
    "cyan",
    "green",
    "yellow",
    "red",
    "magenta",
    "purple",
    "neutral",
)

ICONS = (
    "coins",
    "cash",
    "wallet",
    "bank",
    "credit-card",
    "cart",
    "shop",
    "box-iso",
    "truck",
    "graph-up",
    "graph-down",
    "percentage",
    "user",
    "group",
    "user-crown",
    "building",
    "calendar",
    "clock",
    "hourglass",
    "check-circle",
    "warning-triangle",
    "triangle-flag",
    "trophy",
    "star",
    "rocket",
    "light-bulb",
    "help-circle",
    "task-list",
    "headset-help",
    "mail",
    "phone",
    "globe",
)
