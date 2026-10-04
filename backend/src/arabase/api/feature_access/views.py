"""Admin endpoints for who may use automations, applications and Sanad, under
``/api/arabase/admin/feature-access/`` (docs/FEATURE_ACCESS.md).

Every response carries the whole list, so the settings page renders it as is.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from arabase.api.feature_access.serializers import (
    AddFeatureGrantsSerializer,
    UpdateFeatureAccessSerializer,
)
from arabase.feature_access.exceptions import (
    FeatureAccessGrantDoesNotExist,
    UnknownFeature,
)
from arabase.feature_access.handler import (
    add_grants,
    list_feature_access,
    remove_grant,
    set_everyone,
)
from jadawel.api.decorators import map_exceptions, validate_body

ERROR_FEATURE_DOES_NOT_EXIST = (
    "ERROR_FEATURE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "No feature has this name.",
)
ERROR_FEATURE_GRANT_DOES_NOT_EXIST = (
    "ERROR_FEATURE_GRANT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The feature grant does not exist.",
)
ERRORS = {
    UnknownFeature: ERROR_FEATURE_DOES_NOT_EXIST,
    FeatureAccessGrantDoesNotExist: ERROR_FEATURE_GRANT_DOES_NOT_EXIST,
}
FEATURE = OpenApiParameter(
    name="feature",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.STR,
    description="automation, builder or sanad.",
)
GRANT_ID = OpenApiParameter(
    name="grant_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The grant to remove.",
)
TAGS = ["Arabase admin feature access"]


def _listing() -> Response:
    return Response({"features": list_feature_access()})


class AdminFeatureAccessView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=TAGS,
        operation_id="list_admin_feature_access",
        description="Who may use automations, applications and Sanad.",
    )
    def get(self, request: Request) -> Response:
        return _listing()


class AdminFeatureView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[FEATURE],
        tags=TAGS,
        operation_id="update_admin_feature_access",
        description="Opens a feature to every user, or limits it to staff and "
        "its granted email addresses.",
        request=UpdateFeatureAccessSerializer,
    )
    @map_exceptions(ERRORS)
    @validate_body(UpdateFeatureAccessSerializer)
    def patch(self, request: Request, feature: str, data: dict) -> Response:
        set_everyone(request.user, feature, data["everyone"])
        return _listing()


class AdminFeatureGrantsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[FEATURE],
        tags=TAGS,
        operation_id="add_admin_feature_grants",
        description="Grants a feature to email addresses.",
        request=AddFeatureGrantsSerializer,
    )
    @map_exceptions(ERRORS)
    @validate_body(AddFeatureGrantsSerializer)
    def post(self, request: Request, feature: str, data: dict) -> Response:
        add_grants(request.user, feature, data["emails"])
        return _listing()


class AdminFeatureGrantView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[FEATURE, GRANT_ID],
        tags=TAGS,
        operation_id="delete_admin_feature_grant",
        description="Removes one email address's grant of a feature.",
    )
    @map_exceptions(ERRORS)
    def delete(self, request: Request, feature: str, grant_id: int) -> Response:
        remove_grant(feature, grant_id)
        return _listing()
