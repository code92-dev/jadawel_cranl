from django.db import models

from jadawel.contrib.database.views.models import SORT_ORDER_CHOICES, SORT_ORDER_DESC
from jadawel.contrib.integrations.local_jadawel.models import (
    LocalJadawelFilterableServiceMixin,
    LocalJadawelFilterableSortableMixin,
    LocalJadawelViewService,
)
from jadawel.core.services.models import SearchableServiceMixin

SORT_ON_SERIES = "SERIES"
SORT_ON_GROUP_BY = "GROUP_BY"
SORT_ON_CHOICES = [
    (SORT_ON_SERIES, SORT_ON_SERIES),
    (SORT_ON_GROUP_BY, SORT_ON_GROUP_BY),
]


class LocalJadawelGroupedAggregateRows(
    LocalJadawelViewService,
    LocalJadawelFilterableServiceMixin,
    SearchableServiceMixin,
):
    """
    Configuration for an aggregation that is bucketed by a field.

    The core `LocalJadawelAggregateRows` service returns a single number for the
    whole table. Every chart needs one number *per bucket*, which is what this
    service adds: zero or more `series` (field + aggregation type) computed over
    the groups produced by a `group by` field.

    With no group by configured the service still dispatches and returns one
    bucket per series, which is what makes a single-value chart possible.
    """


class LocalJadawelTableServiceAggregationSeries(models.Model):
    """One field/aggregation pair computed per bucket."""

    service = models.ForeignKey(
        LocalJadawelGroupedAggregateRows,
        related_name="service_aggregation_series",
        on_delete=models.CASCADE,
        help_text="The service this aggregation series belongs to.",
    )
    field = models.ForeignKey(
        "database.Field",
        help_text="The aggregated field.",
        null=True,
        on_delete=models.SET_NULL,
    )
    aggregation_type = models.CharField(
        default="", blank=True, max_length=48, help_text="The field aggregation type."
    )
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ("order", "id")

    def __repr__(self):
        return (
            "<LocalJadawelTableServiceAggregationSeries "
            f"{self.field_id} {self.aggregation_type}>"
        )

    @property
    def key(self) -> str:
        """
        The name this series is addressed by in the dispatch result, in
        `ChartWidget.series_config`, and in a sort's `reference`.

        Derived from the field and aggregation type rather than the series' own
        id so that it survives an export/import round trip: field ids are
        remapped on import, series ids are not.
        """

        return series_key(self.field_id, self.aggregation_type)


def series_key(field_id: int | None, aggregation_type: str) -> str:
    return f"field_{field_id}_{aggregation_type}"


def remap_series_key(key: str, field_mapping: dict) -> str:
    """
    Follows a field id remapping inside a series key, the way an import remaps
    the series themselves. A key that is not `field_<digits>_<rest>`, or whose
    field has no mapping, is returned unchanged.
    """

    parts = key.split("_", 2)
    if len(parts) != 3 or parts[0] != "field" or not parts[1].isdigit():
        return key
    new_field_id = field_mapping.get(int(parts[1]), None)
    if new_field_id is None:
        return key
    return series_key(new_field_id, parts[2])


class LocalJadawelTableServiceAggregationGroupBy(models.Model):
    """The field whose distinct values become the buckets."""

    service = models.ForeignKey(
        LocalJadawelGroupedAggregateRows,
        related_name="service_aggregation_group_bys",
        on_delete=models.CASCADE,
        help_text="The service this group by belongs to.",
    )
    field = models.ForeignKey(
        "database.Field",
        help_text="The field to group the aggregation by.",
        null=True,
        on_delete=models.SET_NULL,
    )
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ("order", "id")

    def __repr__(self):
        return f"<LocalJadawelTableServiceAggregationGroupBy {self.field_id}>"


class LocalJadawelTableServiceAggregationSortBy(models.Model):
    """
    How the buckets are ordered, either by their label (`GROUP_BY`) or by one
    series' value (`SERIES`).
    """

    service = models.ForeignKey(
        LocalJadawelGroupedAggregateRows,
        related_name="service_aggregation_sorts",
        on_delete=models.CASCADE,
        help_text="The service this sort belongs to.",
    )
    sort_on = models.CharField(
        max_length=10,
        choices=SORT_ON_CHOICES,
        default=SORT_ON_SERIES,
        help_text="Whether the sort applies to a series value or the group by field.",
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The series key or group by field reference being sorted on.",
    )
    direction = models.CharField(
        max_length=4,
        choices=SORT_ORDER_CHOICES,
        default=SORT_ORDER_DESC,
        help_text="Indicates the sort order direction.",
    )
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ("order", "id")

    def __repr__(self):
        return (
            "<LocalJadawelTableServiceAggregationSortBy "
            f"{self.sort_on} {self.reference} {self.direction}>"
        )


class LocalJadawelUpcomingRows(
    LocalJadawelViewService,
    LocalJadawelFilterableServiceMixin,
    LocalJadawelFilterableSortableMixin,
    SearchableServiceMixin,
):
    """
    Rows whose date field falls inside a window starting today.

    A list-rows service with a filter could nearly do this, but the relative-date
    filter values are an encoded string (timezone, amount, unit) that a widget
    settings panel has no business assembling. Holding the window as three plain
    fields keeps the widget simple and the query server-side, which matters: the
    alternative is fetching every row and filtering in the browser.
    """

    default_result_count = models.PositiveIntegerField(
        default=10,
        db_default=10,
        help_text="The number of records returned with each page.",
    )
    date_field = models.ForeignKey(
        "database.Field",
        help_text="The date field defining when a record is due.",
        null=True,
        on_delete=models.SET_NULL,
    )
    days_ahead = models.PositiveIntegerField(
        default=7,
        db_default=7,
        help_text="How many days ahead of today to include.",
    )
    include_overdue = models.BooleanField(
        default=True,
        db_default=True,
        help_text="Whether records whose date has already passed are included.",
    )
