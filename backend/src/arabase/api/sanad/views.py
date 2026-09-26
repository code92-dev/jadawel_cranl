"""Sanad (سند) chat API, mounted under ``/api/arabase/sanad/``.

Every endpoint is limited to instance staff who are members of the chat's
workspace, and a chat is only ever visible to the user who started it.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from arabase.api.sanad.errors import (
    ERROR_SANAD_CHAT_BUSY,
    ERROR_SANAD_CHAT_DOES_NOT_EXIST,
    ERROR_SANAD_MODEL_NOT_AVAILABLE,
    ERROR_SANAD_NO_MODEL_AVAILABLE,
    ERROR_SANAD_NOT_ALLOWED,
    ERROR_SANAD_NOTHING_TO_APPROVE,
)
from arabase.api.sanad.serializers import (
    SanadChatSerializer,
    SanadChatWithMessagesSerializer,
    SanadDecisionsSerializer,
    SanadMessageSerializer,
    SendSanadMessageSerializer,
)
from arabase.sanad.exceptions import (
    SanadChatBusy,
    SanadChatDoesNotExist,
    SanadModelNotAvailable,
    SanadNoModelAvailable,
    SanadNotAllowed,
    SanadNothingToApprove,
)
from arabase.sanad.handler import SanadHandler
from jadawel.api.decorators import map_exceptions, validate_body
from jadawel.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from jadawel.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist

COMMON_ERRORS = {
    SanadNotAllowed: ERROR_SANAD_NOT_ALLOWED,
    SanadChatDoesNotExist: ERROR_SANAD_CHAT_DOES_NOT_EXIST,
    WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
    UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
}

WORKSPACE_ID = OpenApiParameter(
    name="workspace_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="The workspace Sanad works in.",
)
CHAT_ID = OpenApiParameter(
    name="chat_id",
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="One of the requesting user's Sanad chats.",
)
TAGS = ["Arabase Sanad"]


class SanadModelsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[WORKSPACE_ID],
        tags=TAGS,
        operation_id="list_sanad_models",
        description="The AI models Sanad can use, as `<provider>/<model>`.",
    )
    @map_exceptions(COMMON_ERRORS)
    def get(self, request: Request, workspace_id: int) -> Response:
        from arabase.sanad.agent import get_available_models

        workspace = SanadHandler().get_workspace(request.user, workspace_id)
        return Response({"models": get_available_models(workspace)})


class SanadChatsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[WORKSPACE_ID],
        tags=TAGS,
        operation_id="list_sanad_chats",
        description="The requesting user's Sanad chats in the workspace.",
        responses={200: SanadChatSerializer(many=True)},
    )
    @map_exceptions(COMMON_ERRORS)
    def get(self, request: Request, workspace_id: int) -> Response:
        handler = SanadHandler()
        workspace = handler.get_workspace(request.user, workspace_id)
        chats = handler.list_chats(request.user, workspace)[:50]
        return Response(SanadChatSerializer(chats, many=True).data)

    @extend_schema(
        parameters=[WORKSPACE_ID],
        tags=TAGS,
        operation_id="create_sanad_chat",
        description="Starts an empty Sanad chat.",
        request=None,
        responses={200: SanadChatWithMessagesSerializer},
    )
    @map_exceptions(COMMON_ERRORS)
    def post(self, request: Request, workspace_id: int) -> Response:
        handler = SanadHandler()
        workspace = handler.get_workspace(request.user, workspace_id)
        chat = handler.create_chat(request.user, workspace)
        return Response(SanadChatWithMessagesSerializer(chat).data)


class SanadChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[CHAT_ID],
        tags=TAGS,
        operation_id="get_sanad_chat",
        description="A chat with its messages. Poll it while a turn is pending.",
        responses={200: SanadChatWithMessagesSerializer},
    )
    @map_exceptions(COMMON_ERRORS)
    def get(self, request: Request, chat_id: int) -> Response:
        chat = SanadHandler().get_chat(request.user, chat_id)
        return Response(SanadChatWithMessagesSerializer(chat).data)

    @extend_schema(
        parameters=[CHAT_ID],
        tags=TAGS,
        operation_id="delete_sanad_chat",
        description="Deletes the chat and its history.",
        responses={204: None},
    )
    @map_exceptions(COMMON_ERRORS)
    def delete(self, request: Request, chat_id: int) -> Response:
        SanadHandler().delete_chat(request.user, chat_id)
        return Response(status=HTTP_204_NO_CONTENT)


class SanadMessagesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[CHAT_ID],
        tags=TAGS,
        operation_id="send_sanad_message",
        description=(
            "Sends a message. Sanad answers asynchronously: the returned "
            "assistant message is `pending` until the turn finishes."
        ),
        request=SendSanadMessageSerializer,
        responses={202: SanadMessageSerializer},
    )
    @map_exceptions(
        {
            **COMMON_ERRORS,
            SanadChatBusy: ERROR_SANAD_CHAT_BUSY,
            SanadNoModelAvailable: ERROR_SANAD_NO_MODEL_AVAILABLE,
            SanadModelNotAvailable: ERROR_SANAD_MODEL_NOT_AVAILABLE,
        }
    )
    @validate_body(SendSanadMessageSerializer)
    def post(self, request: Request, chat_id: int, data: dict) -> Response:
        handler = SanadHandler()
        chat = handler.get_chat(request.user, chat_id)
        context = {k: v for k, v in (data.get("context") or {}).items() if v}
        reply = handler.send_message(
            request.user, chat, data["content"], data["model"], context
        )
        return Response(SanadMessageSerializer(reply).data, status=HTTP_202_ACCEPTED)


class SanadDecisionsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[CHAT_ID],
        tags=TAGS,
        operation_id="decide_sanad_actions",
        description=(
            "Approves or declines the destructive actions a paused turn is "
            "waiting on, then resumes it."
        ),
        request=SanadDecisionsSerializer,
        responses={202: SanadMessageSerializer},
    )
    @map_exceptions(
        {**COMMON_ERRORS, SanadNothingToApprove: ERROR_SANAD_NOTHING_TO_APPROVE}
    )
    @validate_body(SanadDecisionsSerializer)
    def post(self, request: Request, chat_id: int, data: dict) -> Response:
        handler = SanadHandler()
        chat = handler.get_chat(request.user, chat_id)
        decisions = {d["tool_call_id"]: d["approved"] for d in data["decisions"]}
        message = handler.decide(request.user, chat, decisions)
        return Response(SanadMessageSerializer(message).data, status=HTTP_202_ACCEPTED)
