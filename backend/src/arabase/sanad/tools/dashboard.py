"""Sanad's dashboard tools: create dashboards and their widgets.

A widget is two things the editor saves separately: the widget (title, size,
chart type, target…) and the data source it owns (table, view, field,
aggregation, grouping). One tool call sets both, through the same serializers,
action types and undo history as the editor, then dispatches the data source
once so the model sees what the widget will show. They are offered only once
the ``dashboards`` skill is loaded.
"""

import json
from typing import Literal, Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import SanadEndpoint, SanadTool

SKILL = "dashboards"

WIDGET_TYPES = ("summary", "chart", "progress", "records_list", "upcoming_dates")

PREVIEW_CHARACTERS = 1200
"""Enough of a dispatch result to judge a widget, not enough to flood the chat."""

SORTS = {
    "value_desc": ("SERIES", "DESC"),
    "value_asc": ("SERIES", "ASC"),
    "label_asc": ("GROUP_BY", "ASC"),
    "label_desc": ("GROUP_BY", "DESC"),
}


class SeriesInput(BaseModel):
    field_id: int = Field(..., description="The field to aggregate.")
    aggregation_type: str = Field(
        ..., description="sum, average, count, min, max, median, unique_count…"
    )
    label: Optional[str] = Field(None, description="Legend label for this series.")
    color: Optional[str] = Field(None, description="A #rrggbb colour.")


class WidgetSettings(BaseModel):
    """Everything a widget can be set up with; each type reads its own part."""

    title: Optional[str] = Field(None, description="The widget title.")
    description: Optional[str] = Field(
        None, description="One line under the title: what it measures, the period."
    )
    width: Optional[int] = Field(
        None, ge=1, le=3, description="1 = a third of the row, 3 = the full row."
    )
    height: Optional[int] = Field(None, ge=1, le=3, description="1 short … 3 tall.")
    table_id: Optional[int] = Field(None, description="The table the data comes from.")
    view_id: Optional[int] = Field(
        None, description="A view of that table whose filters (and sorts) apply."
    )
    field_id: Optional[int] = Field(
        None, description="summary/progress: the field to aggregate."
    )
    aggregation_type: Optional[str] = Field(
        None, description="summary/progress: how to aggregate field_id."
    )
    chart_type: Optional[Literal["bar", "line", "pie", "doughnut"]] = None
    group_by_field_id: Optional[int] = Field(
        None, description="chart: the field whose values become the categories."
    )
    series: Optional[list[SeriesInput]] = Field(
        None, description="chart: 1-5 aggregated values drawn per category."
    )
    sort: Optional[Literal["value_desc", "value_asc", "label_asc", "label_desc"]] = (
        Field(None, description="chart: order of the categories.")
    )
    show_legend: Optional[bool] = None
    target_value: Optional[float] = Field(
        None, gt=0, description="progress: the value that counts as 100%."
    )
    display_style: Optional[Literal["bar", "ring"]] = None
    warning_threshold: Optional[int] = Field(
        None, ge=0, description="progress: % from which it is no longer at risk."
    )
    success_threshold: Optional[int] = Field(
        None, ge=0, description="progress: % from which the goal counts as met."
    )
    field_ids: Optional[list[int]] = Field(
        None, description="records_list/upcoming_dates: up to 6 fields to show."
    )
    date_field_id: Optional[int] = Field(
        None, description="upcoming_dates: the date that makes a row due."
    )
    days_ahead: Optional[int] = Field(
        None, ge=1, le=365, description="upcoming_dates: how far ahead to look."
    )
    include_overdue: Optional[bool] = Field(
        None, description="upcoming_dates: also list rows already past due."
    )
    row_count: Optional[int] = Field(
        None, ge=1, le=100, description="records_list/upcoming_dates: rows shown."
    )


WIDGET_FIELDS = {
    "summary": (),
    "chart": ("chart_type", "show_legend"),
    "progress": (
        "target_value",
        "display_style",
        "warning_threshold",
        "success_threshold",
    ),
    "records_list": ("field_ids",),
    "upcoming_dates": ("field_ids",),
}


def _widget_values(widget_type: str, settings: WidgetSettings) -> dict:
    values = {
        name: getattr(settings, name)
        for name in ("title", "description", "width", "height")
        + WIDGET_FIELDS[widget_type]
        if getattr(settings, name) is not None
    }
    if widget_type == "chart" and settings.series is not None:
        from arabase.integrations.local_jadawel.models import series_key

        values["series_config"] = {
            series_key(item.field_id, item.aggregation_type): {
                key: value
                for key, value in (("label", item.label), ("color", item.color))
                if value
            }
            for item in settings.series
            if item.label or item.color
        }
    return values


def _source_values(widget_type: str, settings: WidgetSettings, widget) -> dict:
    """The data source values the settings change (none: leave it as it is)."""

    values = {}
    if settings.table_id is not None:
        values["table_id"] = settings.table_id
    if "view_id" in settings.model_fields_set:
        values["view_id"] = settings.view_id
    if widget_type in ("summary", "progress"):
        for name in ("field_id", "aggregation_type"):
            if getattr(settings, name) is not None:
                values[name] = getattr(settings, name)
    elif widget_type == "chart":
        if settings.series is not None:
            values["aggregation_series"] = [
                {"field_id": item.field_id, "aggregation_type": item.aggregation_type}
                for item in settings.series
            ]
        if settings.group_by_field_id is not None:
            values["aggregation_group_bys"] = [{"field_id": settings.group_by_field_id}]
        if settings.sort is not None:
            sort_on, direction = SORTS[settings.sort]
            series = settings.series or [
                item
                for item in widget.data_source.service.specific.service_aggregation_series.all()
            ]
            reference = ""
            if sort_on == "SERIES" and series:
                first = series[0]
                reference = f"field_{first.field_id}_{first.aggregation_type}"
            values["aggregation_sorts"] = [
                {"sort_on": sort_on, "reference": reference, "direction": direction}
            ]
    elif widget_type in ("records_list", "upcoming_dates"):
        if settings.row_count is not None:
            values["default_result_count"] = settings.row_count
        if widget_type == "upcoming_dates":
            for name in ("date_field_id", "days_ahead", "include_overdue"):
                if getattr(settings, name) is not None:
                    values[name] = getattr(settings, name)
    return values


REQUIRED_SETTINGS = {
    "summary": ("field_id", "aggregation_type"),
    "chart": ("group_by_field_id", "series"),
    "progress": ("field_id", "aggregation_type", "target_value"),
    "records_list": (),
    "upcoming_dates": ("date_field_id",),
}
"""What each widget type cannot show anything without. Asked for up front, so a
widget is set up in one call rather than created empty and patched field by
field."""


def _check_complete(widget_type: str, settings: "WidgetSettings") -> None:
    missing = [
        name
        for name in REQUIRED_SETTINGS[widget_type]
        if getattr(settings, name) in (None, [])
    ]
    if missing:
        raise ValueError(
            f"A {widget_type} widget needs {', '.join(missing)} in this same "
            "call. Send every setting of the widget at once."
        )


def _get_dashboard(endpoint: SanadEndpoint, dashboard_id: int):
    from arabase.sanad.tools.base import get_application

    return get_application(endpoint, dashboard_id, "dashboard")


def _get_widget(endpoint: SanadEndpoint, widget_id: int):
    from jadawel.contrib.dashboard.widgets.exceptions import WidgetDoesNotExist
    from jadawel.contrib.dashboard.widgets.service import WidgetService

    widget = WidgetService().get_widget(endpoint.user, widget_id)
    if widget.dashboard.workspace_id != endpoint.workspace.id:
        raise WidgetDoesNotExist(widget_id)
    return widget.specific


def _integration_id(dashboard) -> int:
    from jadawel.core.integrations.models import Integration

    integration = (
        Integration.objects.filter(application=dashboard, trashed=False)
        .order_by("id")
        .first()
    )
    if integration is None:
        raise ValueError("The dashboard has no data connection; recreate it.")
    return integration.id


def _configure_source(endpoint: SanadEndpoint, widget, values: dict) -> None:
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.dashboard.api.data_sources.serializers import (
        UpdateDashboardDataSourceSerializer,
    )
    from jadawel.contrib.dashboard.data_sources.actions import (
        UpdateDashboardDataSourceActionType,
    )
    from jadawel.core.services.registries import service_type_registry

    if not values:
        return
    service = widget.data_source.service.specific
    service_type = service.get_type()
    if not service.integration_id:
        values["integration_id"] = _integration_id(widget.dashboard)
    data = validate_data_custom_fields(
        service_type.type,
        service_type_registry,
        {"type": service_type.type, **values},
        base_serializer_class=UpdateDashboardDataSourceSerializer,
        return_validated=True,
    )
    data.pop("type", None)
    UpdateDashboardDataSourceActionType.do(
        endpoint.user, widget.data_source_id, service_type, data
    )


def _preview(endpoint: SanadEndpoint, widget) -> object:
    """What the widget shows now, or why it cannot show anything."""

    from django.http import HttpRequest

    from jadawel.contrib.dashboard.data_sources.dispatch_context import (
        DashboardDispatchContext,
    )
    from jadawel.contrib.dashboard.data_sources.service import (
        DashboardDataSourceService,
    )

    request = HttpRequest()
    request.user = endpoint.user
    try:
        result = DashboardDataSourceService().dispatch_data_source(
            endpoint.user,
            widget.data_source_id,
            DashboardDispatchContext(request, widget),
        )
    except Exception as exc:  # noqa: BLE001 - reported so the model can fix it
        return {"error": f"{exc.__class__.__name__}: {str(exc)[:300]}"}
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) <= PREVIEW_CHARACTERS:
        return result
    return {"truncated": text[:PREVIEW_CHARACTERS]}


def _widget_summary(endpoint: SanadEndpoint, widget, preview: bool = True) -> dict:
    from jadawel.contrib.dashboard.api.widgets.serializers import WidgetSerializer
    from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

    data = dict(widget_type_registry.get_serializer(widget, WidgetSerializer).data)
    service = widget.data_source.service.specific
    source = {"table_id": getattr(service, "table_id", None)}
    for name in (
        "view_id",
        "field_id",
        "aggregation_type",
        "date_field_id",
        "days_ahead",
        "include_overdue",
        "default_result_count",
    ):
        if hasattr(service, name):
            source[name] = getattr(service, name)
    if hasattr(service, "service_aggregation_series"):
        source["series"] = [
            {"field_id": s.field_id, "aggregation_type": s.aggregation_type}
            for s in service.service_aggregation_series.all()
        ]
        source["group_by_field_ids"] = [
            g.field_id for g in service.service_aggregation_group_bys.all()
        ]
    summary = {
        "widget_id": widget.id,
        "dashboard_id": widget.dashboard_id,
        "type": data["type"],
        "title": data["title"],
        "description": data.get("description", ""),
        "width": data.get("width"),
        "height": data.get("height"),
        "settings": {
            key: value
            for key, value in data.items()
            if key
            not in (
                "id",
                "type",
                "title",
                "description",
                "width",
                "height",
                "dashboard_id",
                "order",
                "data_source_id",
            )
        },
        "data": source,
    }
    if preview:
        summary["shows_now"] = _preview(endpoint, widget)
    return summary


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class CreateDashboardInput(BaseModel):
    name: str = Field(..., description="The dashboard name.")


def create_dashboard(endpoint: SanadEndpoint, args: CreateDashboardInput) -> dict:
    from jadawel.core.actions import CreateApplicationActionType

    with transaction.atomic():
        # `init_with_data` gives the dashboard its data connection, as the
        # "add new" menu does.
        dashboard = CreateApplicationActionType.do(
            endpoint.user,
            endpoint.workspace,
            "dashboard",
            name=args.name,
            init_with_data=True,
        )
    return {
        "dashboard_id": dashboard.id,
        "application_id": dashboard.id,
        "name": dashboard.name,
    }


class GetDashboardInput(BaseModel):
    dashboard_id: int = Field(..., description="The dashboard to read.")
    preview: bool = Field(
        False, description="Also show what every widget displays now."
    )


def get_dashboard(endpoint: SanadEndpoint, args: GetDashboardInput) -> dict:
    from jadawel.contrib.dashboard.widgets.service import WidgetService

    dashboard = _get_dashboard(endpoint, args.dashboard_id)
    widgets = WidgetService().get_widgets(endpoint.user, dashboard.id)
    return {
        "dashboard_id": dashboard.id,
        "application_id": dashboard.id,
        "name": dashboard.name,
        "widgets": [
            _widget_summary(endpoint, widget.specific, preview=args.preview)
            for widget in widgets
        ],
    }


class AddDashboardWidgetInput(WidgetSettings):
    dashboard_id: int = Field(..., description="The dashboard to add it to.")
    type: Literal["summary", "chart", "progress", "records_list", "upcoming_dates"]
    title: str = Field(..., description="The widget title.")
    table_id: int = Field(..., description="The table the data comes from.")


def add_dashboard_widget(
    endpoint: SanadEndpoint, args: AddDashboardWidgetInput
) -> dict:
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.dashboard.api.widgets.serializers import (
        CreateWidgetSerializer,
    )
    from jadawel.contrib.dashboard.widgets.actions import CreateWidgetActionType
    from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

    dashboard = _get_dashboard(endpoint, args.dashboard_id)
    _check_complete(args.type, args)
    data = validate_data_custom_fields(
        args.type,
        widget_type_registry,
        {"type": args.type, **_widget_values(args.type, args)},
        base_serializer_class=CreateWidgetSerializer,
        return_validated=True,
    )
    data.pop("type", None)
    with transaction.atomic():
        widget = CreateWidgetActionType.do(endpoint.user, dashboard.id, args.type, data)
        widget = _get_widget(endpoint, widget.id)
        _configure_source(endpoint, widget, _source_values(args.type, args, widget))
    return _widget_summary(endpoint, _get_widget(endpoint, widget.id))


class UpdateDashboardWidgetInput(WidgetSettings):
    widget_id: int = Field(..., description="The widget to change.")


def update_dashboard_widget(
    endpoint: SanadEndpoint, args: UpdateDashboardWidgetInput
) -> dict:
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.dashboard.api.widgets.serializers import (
        UpdateWidgetSerializer,
    )
    from jadawel.contrib.dashboard.widgets.actions import UpdateWidgetActionType
    from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

    widget = _get_widget(endpoint, args.widget_id)
    widget_type = widget.get_type().type
    values = _widget_values(widget_type, args)
    with transaction.atomic():
        if values:
            data = validate_data_custom_fields(
                widget_type,
                widget_type_registry,
                values,
                base_serializer_class=UpdateWidgetSerializer,
                partial=True,
                return_validated=True,
            )
            UpdateWidgetActionType.do(endpoint.user, widget.id, widget_type, data)
        _configure_source(endpoint, widget, _source_values(widget_type, args, widget))
    return _widget_summary(endpoint, _get_widget(endpoint, widget.id))


class DeleteDashboardWidgetInput(BaseModel):
    widget_id: int = Field(..., description="The widget to delete.")


def delete_dashboard_widget(
    endpoint: SanadEndpoint, args: DeleteDashboardWidgetInput
) -> dict:
    from jadawel.contrib.dashboard.widgets.actions import DeleteWidgetActionType

    widget = _get_widget(endpoint, args.widget_id)
    with transaction.atomic():
        DeleteWidgetActionType.do(endpoint.user, widget.id)
    return {"deleted_widget_id": widget.id, "dashboard_id": widget.dashboard_id}


def get_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "create_dashboard",
            "Create an empty dashboard in the workspace.",
            CreateDashboardInput,
            create_dashboard,
            skill=SKILL,
        ),
        SanadTool(
            "get_dashboard",
            "Read a dashboard's widgets and their settings; preview=true also "
            "shows what each displays.",
            GetDashboardInput,
            get_dashboard,
            skill=SKILL,
        ),
        SanadTool(
            "add_dashboard_widget",
            "Add a widget (summary, chart, progress, records_list, "
            "upcoming_dates) fully set up in one call — title, description, "
            "size, table, view and the type's own settings; the result shows "
            "what it displays.",
            AddDashboardWidgetInput,
            add_dashboard_widget,
            skill=SKILL,
        ),
        SanadTool(
            "update_dashboard_widget",
            "Change a widget's look or data; give only what changes.",
            UpdateDashboardWidgetInput,
            update_dashboard_widget,
            skill=SKILL,
        ),
        SanadTool(
            "delete_dashboard_widget",
            "Delete a widget. Needs the user's approval.",
            DeleteDashboardWidgetInput,
            delete_dashboard_widget,
            skill=SKILL,
        ),
    ]
