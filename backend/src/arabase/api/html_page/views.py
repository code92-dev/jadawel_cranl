from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from arabase.api.html_page.errors import ERROR_HTML_PAGE_DOES_NOT_EXIST
from arabase.mcp.protection.artifact_boundary import (
    artifact_rest_boundary,
    page_feed_projection,
)
from arabase.mcp.protection.models import ArtifactAudience
from arabase.views.models import HtmlPageView
from jadawel.api.decorators import map_exceptions, validate_query_parameters
from jadawel.api.errors import ERROR_USER_NOT_IN_GROUP
from jadawel.api.schemas import get_error_schema
from jadawel.api.search.serializers import SearchQueryParamSerializer
from jadawel.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from jadawel.contrib.database.api.views.errors import (
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
)
from jadawel.contrib.database.api.views.utils import (
    get_hidden_field_ids_for_view_user,
    get_public_view_authorization_token,
)
from jadawel.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from jadawel.contrib.database.views.exceptions import (
    NoAuthorizationToPubliclySharedView,
    ViewDoesNotExist,
)
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.contrib.database.views.operations import ListViewRowsOperationType
from jadawel.contrib.database.views.registries import view_type_registry
from jadawel.contrib.database.views.signals import view_loaded
from jadawel.contrib.database.views.utils import check_permissions_with_view_fallback
from jadawel.core.exceptions import UserNotInWorkspace

SEARCH_PARAM = OpenApiParameter(
    name="search",
    location=OpenApiParameter.QUERY,
    type=OpenApiTypes.STR,
    description="If provided only rows matching the search query are returned.",
)


def _feed_response(rows_serializer_data, total_count: int, row_limit: int) -> Response:
    """The shape the page runtime consumes.

    Deliberately not paginated. A page is a rendering surface that reads the
    whole feed at once, and the feed is already bounded by the view's
    ``row_limit``; adding limit/offset would push paging logic into every
    AI-authored page for no benefit. ``truncated`` is what tells an author their
    page is only seeing part of the table, rather than leaving them to wonder.
    """

    return Response(
        {
            "count": total_count,
            "row_limit": row_limit,
            "truncated": total_count > row_limit,
            "results": rows_serializer_data,
        }
    )


class HtmlPageViewRowsView(APIView):
    """The data feed for a page view, for a signed-in workspace member."""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the rows of this page view.",
            ),
            SEARCH_PARAM,
        ],
        tags=["Database table page view"],
        operation_id="list_database_table_html_page_view_rows",
        description=(
            "Returns the rows that back the page view, honouring the view's "
            "filters, sorts and hidden fields, capped at the view's `row_limit`."
        ),
        responses={
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_HTML_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_HTML_PAGE_DOES_NOT_EXIST,
        }
    )
    @validate_query_parameters(SearchQueryParamSerializer, return_validated=True)
    def get(self, request: Request, view_id: int, query_params) -> Response:
        view_handler = ViewHandler()
        view = view_handler.get_view_as_user(
            request.user,
            view_id,
            HtmlPageView,
            base_queryset=HtmlPageView.objects.prefetch_related("viewsort_set"),
        )

        check_permissions_with_view_fallback(
            ListRowsDatabaseTableOperationType.type,
            ListViewRowsOperationType.type,
            request.user,
            view.table,
            view,
        )

        model = view.table.get_model()
        hidden_field_ids = get_hidden_field_ids_for_view_user(request.user, view)
        with artifact_rest_boundary():
            allowed_field_ids = page_feed_projection(
                view,
                audience=ArtifactAudience.AUTHENTICATED,
                user=request.user,
                search=query_params.get("search"),
            )

        only_search_by_field_ids = None
        if hidden_field_ids:
            only_search_by_field_ids = [
                field_id
                for field_id in model._field_objects.keys()
                if field_id not in hidden_field_ids
            ]
        if allowed_field_ids is not None:
            only_search_by_field_ids = sorted(
                set(only_search_by_field_ids or model._field_objects.keys())
                & allowed_field_ids
            )

        queryset = view_handler.get_queryset(
            request.user,
            view,
            query_params.get("search"),
            model,
            search_mode=query_params.get("search_mode"),
            only_search_by_field_ids=only_search_by_field_ids,
        )

        total_count = queryset.count()
        rows = queryset[: view.row_limit]

        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=allowed_field_ids,
            exclude_field_ids=hidden_field_ids,
        )

        view_loaded.send(
            sender=self,
            table=view.table,
            view=view,
            table_model=model,
            user=request.user,
        )

        return _feed_response(
            serializer_class(rows, many=True).data, total_count, view.row_limit
        )


class PublicHtmlPageViewRowsView(APIView):
    """The same feed for a visitor holding the public link.

    ``get_public_view_by_slug`` is what enforces the password: without a valid
    token for a protected view it raises, which maps to a 401 and sends the
    visitor to the password page.
    """

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="The slug of the publicly shared page view.",
            ),
            SEARCH_PARAM,
        ],
        tags=["Database table page view"],
        operation_id="public_list_database_table_html_page_view_rows",
        description=(
            "Returns the rows that back a publicly shared page view. Only fields "
            "that are visible in the view are included."
        ),
        responses={
            401: get_error_schema(["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"]),
            404: get_error_schema(["ERROR_HTML_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_HTML_PAGE_DOES_NOT_EXIST,
            NoAuthorizationToPubliclySharedView: (
                ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW
            ),
        }
    )
    @transaction.atomic
    @validate_query_parameters(SearchQueryParamSerializer, return_validated=True)
    def get(self, request: Request, slug: str, query_params) -> Response:
        view_handler = ViewHandler()
        view = view_handler.get_public_view_by_slug(
            request.user,
            slug,
            HtmlPageView,
            authorization_token=get_public_view_authorization_token(request),
        )
        view_type = view_type_registry.get_by_model(view)
        model = view.table.get_model()

        with artifact_rest_boundary():
            allowed_field_ids = page_feed_projection(
                view,
                audience=ArtifactAudience.PUBLIC,
                user=request.user,
                search=query_params.get("search"),
            )

        (
            queryset,
            field_ids,
            _publicly_visible_field_options,
        ) = view_handler.get_public_rows_queryset_and_field_ids(
            view,
            search=query_params.get("search"),
            table_model=model,
            view_type=view_type,
            search_mode=query_params.get("search_mode"),
        )

        total_count = queryset.count()
        rows = queryset[: view.row_limit]

        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=field_ids,
            exclude_field_ids=(
                set(field_ids) - allowed_field_ids
                if allowed_field_ids is not None
                else None
            ),
        )

        return _feed_response(
            serializer_class(rows, many=True).data, total_count, view.row_limit
        )
