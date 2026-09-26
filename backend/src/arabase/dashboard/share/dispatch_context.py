"""What a visitor holding only a share slug is allowed to read.

A signed-in member dispatching a data source already has read access to the
whole table, so :class:`DashboardDispatchContext` deliberately places no limit
on which fields come back: its ``public_allowed_properties`` returns ``None``,
and ``None`` means "every field" all the way down to the row serializer.

A visitor holding a share link is in a different position. They are authorised
to see *the dashboard* — which is the fields its widgets display, and nothing
else. Reusing the private context for them turns a widget showing one column
into a reader for every other column of the same rows, because the dispatch
result is serialized from the table model rather than from the widget.

This module builds the explicit allow-list that closes that gap, and the
dispatch context that carries it. The same list is handed to the data source
serializer so the schema a visitor receives describes only the fields they can
actually fetch — otherwise the column *names* would still leak even though the
values no longer do.
"""

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set

from django.http import HttpRequest

from jadawel.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from jadawel.contrib.dashboard.data_sources.handler import DashboardDataSourceHandler
from jadawel.contrib.dashboard.widgets.handler import WidgetHandler

if TYPE_CHECKING:
    from jadawel.contrib.dashboard.data_sources.models import DashboardDataSource
    from jadawel.contrib.dashboard.models import Dashboard
    from jadawel.contrib.dashboard.widgets.models import Widget
    from jadawel.core.services.models import Service

AGGREGATION_RESULT_PROPERTY = "result"
"""The aggregate rows service addresses its single value by this name rather
than by a field, and returns nothing at all when it is absent from the
allow-list. It carries no field data, so every service may hold it."""

FIELD_PROPERTY_PREFIX = "field_"


def get_public_allowed_properties(
    dashboard: "Dashboard",
    *,
    widgets: Optional[Iterable["Widget"]] = None,
    data_sources: Optional[Iterable["DashboardDataSource"]] = None,
) -> Dict[int, List[str]]:
    """
    The property names each of a dashboard's services may expose publicly,
    keyed by service id.

    A data source that no widget renders gets an empty list rather than being
    omitted: a missing key and an empty list are read the same way downstream,
    and both fail closed. That is the intended outcome — an orphaned data
    source has no widget to justify any field.

    Each entry depends only on its own data source and the widgets rendering
    it, so the entries built for some of the data sources are exactly the ones
    the whole dashboard's map holds for them.

    :param dashboard: The dashboard being shared.
    :param widgets: The dashboard's specific widgets, when the caller already
        fetched them. Fetched here when omitted.
    :param data_sources: The dashboard's data sources to build entries for.
        Every data source of the dashboard when omitted.
    :return: A mapping of service id to allowed property names.
    """

    if widgets is None:
        widgets = WidgetHandler().get_widgets(dashboard)
    if data_sources is None:
        data_sources = DashboardDataSourceHandler().get_data_sources(dashboard)
    widgets = list(widgets)
    data_sources = list(data_sources)

    widgets_by_data_source: Dict[int, List["Widget"]] = {}
    for widget in widgets:
        data_source_id = getattr(widget, "data_source_id", None)
        if data_source_id is not None:
            widgets_by_data_source.setdefault(data_source_id, []).append(widget)

    allowed: Dict[int, List[str]] = {}
    for data_source in data_sources:
        service = data_source.service.specific

        field_ids: Set[int] = set()
        for widget in widgets_by_data_source.get(data_source.id, []):
            field_ids |= _widget_field_ids(widget, service)
        field_ids |= _service_field_ids(service)

        allowed[data_source.service_id] = [AGGREGATION_RESULT_PROPERTY] + [
            f"{FIELD_PROPERTY_PREFIX}{field_id}" for field_id in sorted(field_ids)
        ]

    return allowed


def _widget_field_ids(widget: "Widget", service: "Service") -> Set[int]:
    """
    The fields a widget renders.

    An empty stored list is not "no fields" — it means the widget falls back to
    the first few fields of the table, which the frontend resolves off the
    schema. The fallback has to be resolved the same way here, or the widget
    would render columns the dispatch refuses to return.
    """

    field_ids = getattr(widget, "field_ids", None)
    if field_ids is None:
        return set()
    if field_ids:
        return set(field_ids)

    count = getattr(widget.get_type(), "default_displayed_field_count", 0)
    return set(_ordered_schema_field_ids(service)[:count])


def _service_field_ids(service: "Service") -> Set[int]:
    """
    The fields a service needs regardless of which widget renders it.

    These are configuration rather than display: the aggregated field, the date
    column an agenda is built from, the series and buckets of a chart. Leaving
    them out would restrict the queryset below what the service reads and break
    the dispatch rather than merely hiding a column.
    """

    field_ids: Set[int] = set()

    for attribute in ("field_id", "date_field_id"):
        field_id = getattr(service, attribute, None)
        if field_id:
            field_ids.add(field_id)

    for relation in ("service_aggregation_series", "service_aggregation_group_bys"):
        manager = getattr(service, relation, None)
        if manager is not None:
            field_ids.update(
                field_id
                for field_id in manager.values_list("field_id", flat=True)
                if field_id
            )

    return field_ids


def _ordered_schema_field_ids(service: "Service") -> List[int]:
    """
    The service's field ids in the order the schema lists them, which is the
    order the frontend slices its fallback from.
    """

    service_type = service.get_type()
    schema = service_type.generate_schema(service)
    if not schema:
        return []

    properties = schema.get("properties", None)
    if properties is None:
        properties = schema.get("items", {}).get("properties", {})

    field_ids = []
    for name, definition in properties.items():
        if not name.startswith(FIELD_PROPERTY_PREFIX):
            continue
        # The frontend drops properties with no title, so the fallback it takes
        # skips them too.
        if not (definition or {}).get("title", None):
            continue
        try:
            field_ids.append(int(name[len(FIELD_PROPERTY_PREFIX) :]))
        except ValueError:
            continue

    return field_ids


class PublicDashboardDispatchContext(DashboardDispatchContext):
    """
    The dispatch context for an anonymous visitor to a shared dashboard.

    Identical to the private context except that it answers
    ``public_allowed_properties`` with a real allow-list instead of ``None``.
    Note that the base class declares that member a property; the private
    context defines it as a plain method, which is why its value never reads as
    a dict and every field is returned.
    """

    own_properties = DashboardDispatchContext.own_properties + ["allowed_properties"]

    def __init__(
        self,
        request: Optional[HttpRequest] = None,
        widget: Optional["Widget"] = None,
        allowed_properties: Optional[Dict[int, Iterable[str]]] = None,
    ):
        self.allowed_properties = allowed_properties or {}
        super().__init__(request, widget=widget)

    @property
    def public_allowed_properties(self) -> Dict[str, Dict[int, List[str]]]:
        return {"all": self.allowed_properties}

    def clone(self, **kwargs) -> Any:
        # The base implementation rebuilds the context from `own_properties`
        # alone, which drops the request the dashboard context requires.
        new_values = {
            "request": self.request,
            "widget": self.widget,
            "allowed_properties": self.allowed_properties,
            **kwargs,
        }
        new_context = self.__class__(**new_values)
        new_context.cache = {**self.cache}
        new_context.call_stack = set(self.call_stack)
        return new_context
