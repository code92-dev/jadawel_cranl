"""Admin endpoints for AI provider keys, under ``/api/arabase/admin/generative-ai/``.

Keys are write-only: responses carry whether a key is set and its last
characters, never the key itself.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from arabase.api.generative_ai.serializers import UpdateProviderSettingsSerializer
from arabase.generative_ai.handler import (
    InvalidProviderSettings,
    ProviderNotManaged,
    delete_provider_settings,
    list_provider_settings,
    update_provider_settings,
)
from jadawel.api.decorators import map_exceptions, validate_body

ERROR_AI_PROVIDER_NOT_MANAGED = (
    "ERROR_AI_PROVIDER_NOT_MANAGED",
    HTTP_404_NOT_FOUND,
    "This AI provider cannot be configured here.",
)
ERROR_AI_PROVIDER_SETTINGS_INVALID = (
    "ERROR_AI_PROVIDER_SETTINGS_INVALID",
    HTTP_400_BAD_REQUEST,
    "{e}",
)
ERRORS = {
    ProviderNotManaged: ERROR_AI_PROVIDER_NOT_MANAGED,
    InvalidProviderSettings: ERROR_AI_PROVIDER_SETTINGS_INVALID,
}
PROVIDER = OpenApiParameter(
    name="provider",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.STR,
    description="openai, anthropic, ollama or openrouter.",
)
TAGS = ["Arabase admin AI"]


class AdminGenerativeAIView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=TAGS,
        operation_id="list_admin_ai_providers",
        description="The AI providers administrators can configure.",
    )
    def get(self, request: Request) -> Response:
        return Response({"providers": list_provider_settings()})


class AdminGenerativeAIProviderView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[PROVIDER],
        tags=TAGS,
        operation_id="update_admin_ai_provider",
        description="Changes the given settings of one provider.",
        request=UpdateProviderSettingsSerializer,
    )
    @map_exceptions(ERRORS)
    @validate_body(UpdateProviderSettingsSerializer)
    def patch(self, request: Request, provider: str, data: dict) -> Response:
        update_provider_settings(request.user, provider, **data)
        return Response({"providers": list_provider_settings()})

    @extend_schema(
        parameters=[PROVIDER],
        tags=TAGS,
        operation_id="delete_admin_ai_provider",
        description="Removes every admin setting of one provider.",
    )
    @map_exceptions(ERRORS)
    def delete(self, request: Request, provider: str) -> Response:
        delete_provider_settings(provider)
        return Response({"providers": list_provider_settings()})
