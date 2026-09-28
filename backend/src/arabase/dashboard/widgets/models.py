from django.db import models

from jadawel.contrib.dashboard.widgets.models import Widget

CHART_TYPE_BAR = "bar"
CHART_TYPE_HORIZONTAL_BAR = "horizontal_bar"
CHART_TYPE_LINE = "line"
CHART_TYPE_AREA = "area"
CHART_TYPE_PIE = "pie"
CHART_TYPE_DOUGHNUT = "doughnut"
CHART_TYPE_CHOICES = [
    (CHART_TYPE_BAR, "Bar"),
    (CHART_TYPE_HORIZONTAL_BAR, "Horizontal bar"),
    (CHART_TYPE_LINE, "Line"),
    (CHART_TYPE_AREA, "Area"),
    (CHART_TYPE_PIE, "Pie"),
    (CHART_TYPE_DOUGHNUT, "Doughnut"),
]


class ChartWidget(Widget):
    """
    A widget that renders a grouped aggregation as a bar, line, pie or
    doughnut chart.

    The four chart types are one widget type rather than four, because they all
    need exactly the same configuration and users routinely try one and switch
    to another. The picker still offers four tiles; they differ only in the
    `chart_type` they preset.
    """

    data_source = models.ForeignKey(
        "dashboard.DashboardDataSource",
        on_delete=models.PROTECT,
        help_text="The grouped aggregation this chart renders.",
    )
    chart_type = models.CharField(
        max_length=16,
        choices=CHART_TYPE_CHOICES,
        default=CHART_TYPE_BAR,
        db_default=CHART_TYPE_BAR,
        help_text="How the aggregation is drawn.",
    )
    series_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-series display overrides, keyed by series key "
        "(`field_<id>_<aggregation type>`). Supports `color` and `label`.",
    )
    show_legend = models.BooleanField(
        default=True,
        db_default=True,
        help_text="Whether the chart's legend is shown.",
    )


DISPLAY_STYLE_BAR = "bar"
DISPLAY_STYLE_RING = "ring"
DISPLAY_STYLE_GAUGE = "gauge"
DISPLAY_STYLE_CHOICES = [
    (DISPLAY_STYLE_BAR, "Bar"),
    (DISPLAY_STYLE_RING, "Ring"),
    (DISPLAY_STYLE_GAUGE, "Gauge"),
]


class RecordsListWidget(Widget):
    """
    The most recent rows of a table or view.

    Every operations dashboard starts with a "latest requests" list, and this is
    the cheapest widget in the set: it needs no new service, only a choice of
    which fields to show.
    """

    data_source = models.ForeignKey(
        "dashboard.DashboardDataSource",
        on_delete=models.PROTECT,
        help_text="The rows this widget lists.",
    )
    field_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Ids of the fields to show, in order. Empty means the widget "
        "picks the first few fields of the table itself.",
    )


class ProgressWidget(Widget):
    """
    An aggregation measured against a target.

    Quotas, collection targets and SLA attainment are all the same shape — a
    number over a goal — and a bare number (what the summary widget gives) does
    not answer "are we on track".
    """

    data_source = models.ForeignKey(
        "dashboard.DashboardDataSource",
        on_delete=models.PROTECT,
        help_text="The aggregation this widget measures.",
    )
    target_value = models.DecimalField(
        max_digits=50,
        decimal_places=10,
        default=100,
        db_default=100,
        help_text="The value that counts as 100%.",
    )
    display_style = models.CharField(
        max_length=8,
        choices=DISPLAY_STYLE_CHOICES,
        default=DISPLAY_STYLE_BAR,
        db_default=DISPLAY_STYLE_BAR,
        help_text="Whether progress is drawn as a bar, a ring or a gauge.",
    )
    warning_threshold = models.PositiveIntegerField(
        default=50,
        db_default=50,
        help_text="Percentage at or above which progress is no longer at risk.",
    )
    success_threshold = models.PositiveIntegerField(
        default=100,
        db_default=100,
        help_text="Percentage at or above which progress counts as met.",
    )


class UpcomingDatesWidget(Widget):
    """
    An agenda of rows falling due soon.

    The window itself lives on the data source's service, because narrowing has
    to happen in the query rather than in the browser.
    """

    data_source = models.ForeignKey(
        "dashboard.DashboardDataSource",
        on_delete=models.PROTECT,
        help_text="The upcoming rows this widget lists.",
    )
    field_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Ids of the fields to show alongside the date, in order.",
    )


TEXT_STYLE_SECTION = "section"
TEXT_STYLE_NOTE = "note"
TEXT_STYLE_CALLOUT = "callout"
TEXT_STYLE_CHOICES = [
    (TEXT_STYLE_SECTION, "Section heading"),
    (TEXT_STYLE_NOTE, "Note"),
    (TEXT_STYLE_CALLOUT, "Callout"),
]

TEXT_BODY_MAX_LENGTH = 2000


class TextWidget(Widget):
    """
    Words on the board, with no data behind them: a heading that splits the
    dashboard into sections, a note explaining how to read it, or a highlighted
    callout. Numbers only mean something with context, and until now the only
    place for context was a widget's one-line description.
    """

    body = models.TextField(
        blank=True,
        default="",
        db_default="",
        max_length=TEXT_BODY_MAX_LENGTH,
        help_text="Plain text under the title. Line breaks are kept.",
    )
    text_style = models.CharField(
        max_length=16,
        choices=TEXT_STYLE_CHOICES,
        default=TEXT_STYLE_NOTE,
        db_default=TEXT_STYLE_NOTE,
        help_text="A section heading, a note card or a highlighted callout.",
    )
