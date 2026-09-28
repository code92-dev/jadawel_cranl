from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from jadawel.core.mixins import (
    CreatedAndUpdatedOnMixin,
    FractionOrderableMixin,
    HierarchicalModelMixin,
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
    WithRegistry,
)

if TYPE_CHECKING:
    from jadawel.contrib.dashboard.models import Dashboard

GRID_COLUMNS = 12
"""Columns of the widget board. Exports record it, so a dashboard exported from
the earlier 3-column board is rescaled when it is imported."""

MAX_HEIGHT = 12

LEGACY_GRID_COLUMNS = 3
"""The board before the 12-column grid: 3 columns of 160 px rows. Exports from
then carry no `widget_grid_columns`."""


def rescale_serialized_widgets(widgets: list[dict], grid_columns: int) -> list[dict]:
    """
    Converts exported widget sizes to this board's units. One of the 3 legacy
    columns is 4 of the 12, and one legacy 160 px row is two 72 px rows plus the
    gap between them — the same scaling migration 0005 applied to stored widgets.
    """

    if grid_columns != LEGACY_GRID_COLUMNS:
        return widgets
    scale = GRID_COLUMNS // LEGACY_GRID_COLUMNS
    rescaled = []
    for widget in widgets:
        widget = dict(widget)
        if widget.get("width"):
            widget["width"] = min(GRID_COLUMNS, widget["width"] * scale)
        if widget.get("height"):
            widget["height"] = min(MAX_HEIGHT, widget["height"] * 2)
        rescaled.append(widget)
    return rescaled


class Widget(
    HierarchicalModelMixin,
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    FractionOrderableMixin,
    PolymorphicContentTypeMixin,
    WithRegistry,
    models.Model,
):
    """
    This model represents a dashboard widget. It displays
    information or something the user can interact with.
    """

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    dashboard = models.ForeignKey("dashboard.Dashboard", on_delete=models.CASCADE)
    order = models.DecimalField(
        help_text="Lowest first.",
        max_digits=40,
        decimal_places=20,
        editable=False,
        default=Decimal("1"),
    )
    # Jadawel fork (grid board): spans on a 12-column board of 72 px rows.
    width = models.PositiveSmallIntegerField(
        default=GRID_COLUMNS,
        validators=[MinValueValidator(1), MaxValueValidator(GRID_COLUMNS)],
    )
    height = models.PositiveSmallIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_HEIGHT)],
    )
    appearance = models.JSONField(
        default=dict,
        blank=True,
        help_text="Presentation options the frontend reads, such as the accent "
        "colour, icon and number format.",
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="dashboard_widgets",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("order", "id")

    @staticmethod
    def get_type_registry():
        from .registries import widget_type_registry

        return widget_type_registry

    def get_parent(self):
        return self.dashboard

    @classmethod
    def get_last_order(
        cls,
        dashboard: "Dashboard",
    ):
        """
        Returns the last order for the given page.

        :param dashboard: The dashboard we want the order for.
        :param base_queryset: The base queryset to use.
        :return: The last order.
        """

        return cls.get_last_orders(dashboard)[0]

    @classmethod
    def get_last_orders(
        cls,
        dashboard: "Dashboard",
        amount=1,
    ):
        """
        Returns the last orders for the given dashboard.

        :param dashboard: The dashboard we want the order for.
        :param amount: The number of orders you wish to have returned
        :return: The last order.
        """

        queryset = Widget.objects.filter(dashboard=dashboard)
        return cls.get_highest_order_of_queryset(queryset, amount=amount)


class SummaryWidget(Widget):
    data_source = models.ForeignKey(
        "dashboard.DashboardDataSource",
        on_delete=models.PROTECT,
        help_text="Data source for fetching the result to display.",
    )
