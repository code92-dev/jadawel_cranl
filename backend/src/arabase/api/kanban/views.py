"""API for the kanban view type.

Two endpoints, both scoped to a view id and both gated by the same row-list
permission the gallery rows endpoint uses:

* ``GET /api/database/views/kanban/{view_id}/`` — the board definition: one
  stack per select option of the view's single select field, plus the stack
  of rows without a value, each with the row count the column header shows.
* ``GET /api/database/views/kanban/{view_id}/stacks/{select_option_id}/`` —
  one page of rows for a single stack. ``select_option_id`` is the id of a
  select option, or the literal ``null`` for rows without a value.
"""

from django.db.models import Count

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from arabase.api.kanban.errors import (
    ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD,
    ERROR_KANBAN_VIEW_STACK_DOES_NOT_EXIST,
)
from arabase.api.kanban.exceptions import (
    KanbanViewHasNoSingleSelectField,
    KanbanViewStackDoesNotExist,
)
from arabase.kanban.models import KanbanView
from jadawel.api.decorators import map_exceptions
from jadawel.api.errors import ERROR_USER_NOT_IN_GROUP
from jadawel.api.schemas import get_error_schema
from jadawel.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from jadawel.contrib.database.api.views.errors import (
    ERROR_VIEW_DOES_NOT_EXIST,
)
from jadawel.contrib.database.api.views.utils import get_hidden_field_ids_for_view_user
from jadawel.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from jadawel.contrib.database.views.exceptions import ViewDoesNotExist
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.contrib.database.views.operations import ListViewRowsOperationType
from jadawel.contrib.database.views.registries import view_type_registry
from jadawel.contrib.database.views.signals import view_loaded
from jadawel.contrib.database.views.utils import check_permissions_with_view_fallback
from jadawel.core.exceptions import UserNotInWorkspace


class KanbanLimitOffsetPagination(LimitOffsetPagination):
    """One page of cards per stack; mirrors the gallery's pagination."""

    default_limit = 40
    max_limit = 100


def _get_kanban_view(request: Request, view_id: int) -> KanbanView:
    """Returns the kanban view once the user may list its rows.

    Both endpoints start with the same two checks, in this order: the view
    lookup (``ViewDoesNotExist``, ``UserNotInWorkspace``), then the row-list
    permission with the view fallback the gallery rows endpoint uses.
    """

    view = ViewHandler().get_view_as_user(
        request.user,
        view_id,
        KanbanView,
        base_queryset=KanbanView.objects.prefetch_related("viewsort_set"),
    )
    check_permissions_with_view_fallback(
        ListRowsDatabaseTableOperationType.type,
        ListViewRowsOperationType.type,
        request.user,
        view.table,
        view,
    )
    return view


class KanbanViewView(APIView):
    permission_classes = ()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the board of the kanban view related to the "
                "provided value.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided, the stack counts only include rows that "
                "match the search query.",
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="get_database_table_kanban_view",
        description=(
            "Returns the stacks of the kanban view related to the provided "
            "`view_id`: one per select option of the configured single select "
            "field, plus the stack of rows without a value. Each stack carries "
            "the row count shown in its header."
        ),
        responses={
            200: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_VIEW_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
        }
    )
    def get(self, request: Request, view_id: int) -> Response:
        """Lists the stacks (columns) of a kanban view with their row counts."""

        view = _get_kanban_view(request, view_id)

        search = request.GET.get("search")
        model = view.table.get_model()
        view_loaded.send(
            sender=self,
            table=view.table,
            view=view,
            table_model=model,
            user=request.user,
        )

        stacks = []
        if view.single_select_field_id is not None:
            select_field = view.single_select_field.specific
            field_name = f"field_{select_field.id}"

            queryset = ViewHandler().get_queryset(
                request.user,
                view,
                search,
                model,
                apply_sorts=False,
                apply_filters=True,
            )
            # `.order_by()` clears the row model's Meta ordering, which would
            # otherwise leak into the GROUP BY and split an option into one
            # group per distinct row order.
            counts_by_option_id = dict(
                queryset.order_by()
                .values(f"{field_name}__id")
                .annotate(total=Count("id"))
                .values_list(f"{field_name}__id", "total")
            )
            counts_by_option_id = {
                option_id: total
                for option_id, total in counts_by_option_id.items()
                if option_id is not None
            }
            # The NULL stack keeps its own COUNT over distinct rows. A link row
            # or multiple select filter or search can make the grouped query
            # count a row once per match, or aggregate it per option, so its
            # None bucket can differ from this count.
            null_count = queryset.filter(**{f"{field_name}__isnull": True}).count()

            stacks = [
                {
                    "id": option.id,
                    "title": option.value,
                    "color": option.color,
                    "count": counts_by_option_id.get(option.id, 0),
                }
                for option in select_field.select_options.all()
            ]
            stacks.append(
                {"id": None, "title": None, "color": None, "count": null_count}
            )

        # Field options ride the board response so the client can order and
        # filter the card fields without a second request. The base view
        # type's `getVisibleFieldsInOrder` expects them in the view store.
        view_type = view_type_registry.get_by_model(view)
        serializer_class = view_type.get_field_options_serializer_class(
            create_if_missing=True
        )
        field_options = serializer_class(view).data

        return Response({"stacks": stacks, **field_options})


class KanbanStackRowsView(APIView):
    permission_classes = ()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The kanban view the stack belongs to.",
            ),
            OpenApiParameter(
                name="select_option_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="The id of the select option the stack is grouped by, "
                "or `null` for the stack of rows without a value.",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="If provided, only rows that match the search query are "
                "returned.",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines from which offset the rows should be returned.",
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="list_database_table_kanban_view_stack_rows",
        description=(
            "Lists one page of rows of a single stack of the kanban view. "
            "Stored view filters and sorts apply to the rows of every stack."
        ),
        responses={
            200: None,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(
                [
                    "ERROR_VIEW_DOES_NOT_EXIST",
                    "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD",
                    "ERROR_KANBAN_VIEW_STACK_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
            KanbanViewHasNoSingleSelectField: (
                ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD
            ),
            KanbanViewStackDoesNotExist: ERROR_KANBAN_VIEW_STACK_DOES_NOT_EXIST,
        }
    )
    def get(self, request: Request, view_id: int, select_option_id: str) -> Response:
        """Lists one page of rows of a single stack."""

        view = _get_kanban_view(request, view_id)

        if view.single_select_field_id is None:
            raise KanbanViewHasNoSingleSelectField()

        select_field = view.single_select_field.specific
        if select_option_id == "null":
            stack_filter = {f"field_{select_field.id}__isnull": True}
        else:
            try:
                option_id = int(select_option_id)
            except ValueError:
                raise KanbanViewStackDoesNotExist()
            if not select_field.select_options.filter(id=option_id).exists():
                raise KanbanViewStackDoesNotExist()
            stack_filter = {f"field_{select_field.id}__id": option_id}

        search = request.GET.get("search")
        model = view.table.get_model()
        hidden_field_ids = get_hidden_field_ids_for_view_user(request.user, view)
        only_search_by_field_ids = None
        if hidden_field_ids:
            only_search_by_field_ids = [
                field_id
                for field_id in model._field_objects.keys()
                if field_id not in hidden_field_ids
            ]

        queryset = ViewHandler().get_queryset(
            request.user,
            view,
            search,
            model,
            apply_sorts=True,
            apply_filters=True,
            only_search_by_field_ids=only_search_by_field_ids,
        )
        queryset = queryset.filter(**stack_filter)

        paginator = KanbanLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            exclude_field_ids=hidden_field_ids,
        )
        serializer = serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        view_loaded.send(
            sender=self,
            table=view.table,
            view=view,
            table_model=model,
            user=request.user,
        )
        return response
