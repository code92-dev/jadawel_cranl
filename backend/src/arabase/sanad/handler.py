"""Sanad chats: who may use them, and how a turn is queued and recorded."""

import logging
from datetime import timedelta
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.utils import timezone

from arabase.sanad.exceptions import (
    SanadChatBusy,
    SanadChatDoesNotExist,
    SanadNotAllowed,
    SanadNothingToApprove,
    SanadTurnTooLong,
)
from arabase.sanad.models import (
    SanadChat,
    SanadMessage,
    SanadMessageRole,
    SanadMessageStatus,
)
from jadawel.core.exceptions import UserNotInWorkspace
from jadawel.core.models import Workspace, WorkspaceUser

logger = logging.getLogger(__name__)

TITLE_LENGTH = 80

STALE_AFTER = timedelta(minutes=10)
"""A turn still pending after this long lost its process (restart, OOM); it is
shown as failed so the chat is usable again. Longer than a turn can last
(``agent.TURN_TIME_LIMIT`` plus one model request)."""

BUSY_STATUSES = (SanadMessageStatus.PENDING, SanadMessageStatus.AWAITING_APPROVAL)


class SanadHandler:
    def check_access(self, user: AbstractUser, workspace: Workspace) -> None:
        """Sanad is staff-only while it is introduced, and workspace-bound.

        :raises SanadNotAllowed: for anyone who is not instance staff.
        :raises UserNotInWorkspace: when the user is not a workspace member.
        """

        if not user.is_staff:
            raise SanadNotAllowed()
        if not WorkspaceUser.objects.filter(user=user, workspace=workspace).exists():
            raise UserNotInWorkspace(user, workspace)

    def get_workspace(self, user: AbstractUser, workspace_id: int) -> Workspace:
        from jadawel.core.handler import CoreHandler

        workspace = CoreHandler().get_workspace(workspace_id)
        self.check_access(user, workspace)
        return workspace

    def list_chats(self, user: AbstractUser, workspace: Workspace):
        self.check_access(user, workspace)
        return SanadChat.objects.filter(user=user, workspace=workspace)

    def create_chat(self, user: AbstractUser, workspace: Workspace) -> SanadChat:
        self.check_access(user, workspace)
        return SanadChat.objects.create(user=user, workspace=workspace)

    def get_chat(self, user: AbstractUser, chat_id: int) -> SanadChat:
        """Return one of the user's own chats.

        :raises SanadChatDoesNotExist: for a missing chat or someone else's.
        """

        try:
            chat = SanadChat.objects.select_related("workspace").get(
                id=chat_id, user=user
            )
        except SanadChat.DoesNotExist:
            raise SanadChatDoesNotExist()
        self.check_access(user, chat.workspace)
        self._fail_stale_turns(chat)
        return chat

    def delete_chat(self, user: AbstractUser, chat_id: int) -> None:
        self.get_chat(user, chat_id).delete()

    def _fail_stale_turns(self, chat: SanadChat) -> None:
        chat.messages.filter(
            status=SanadMessageStatus.PENDING,
            updated_on__lt=timezone.now() - STALE_AFTER,
        ).update(
            status=SanadMessageStatus.ERROR,
            error="SANAD_ERROR_TIMED_OUT",
            updated_on=timezone.now(),
        )

    def _check_not_busy(self, chat: SanadChat) -> None:
        if chat.messages.filter(status__in=BUSY_STATUSES).exists():
            raise SanadChatBusy()

    def send_message(
        self,
        user: AbstractUser,
        chat: SanadChat,
        content: str,
        model: str = "",
        context: Optional[dict] = None,
    ) -> SanadMessage:
        """Record the user's message and queue the assistant's reply.

        :raises SanadChatBusy: while the previous turn has not finished.
        :raises SanadNoModelAvailable, SanadModelNotAvailable: see
            ``resolve_model_choice``.
        """

        from arabase.sanad.agent import resolve_model_choice

        self.check_access(user, chat.workspace)
        model_choice = resolve_model_choice(model, chat.workspace)

        with transaction.atomic():
            chat = SanadChat.objects.select_for_update().get(id=chat.id)
            self._check_not_busy(chat)
            SanadMessage.objects.create(
                chat=chat,
                role=SanadMessageRole.USER,
                content=content,
                context=context or {},
            )
            reply = SanadMessage.objects.create(
                chat=chat,
                role=SanadMessageRole.ASSISTANT,
                status=SanadMessageStatus.PENDING,
                context=context or {},
            )
            chat.model = model_choice
            if not chat.title:
                chat.title = " ".join(content.split())[:TITLE_LENGTH]
            chat.save(update_fields=["model", "title", "updated_on"])
            self._queue(reply)
        return reply

    def decide(
        self, user: AbstractUser, chat: SanadChat, decisions: dict[str, bool]
    ) -> SanadMessage:
        """Approve or decline the tool calls a paused turn is waiting on.

        Every pending call must get a decision, so the model never resumes with
        a half-answered request.

        :raises SanadNothingToApprove: when no turn is paused.
        """

        self.check_access(user, chat.workspace)
        with transaction.atomic():
            message = (
                SanadMessage.objects.select_for_update()
                .filter(chat=chat, status=SanadMessageStatus.AWAITING_APPROVAL)
                .last()
            )
            if message is None:
                raise SanadNothingToApprove()
            expected = {
                call["tool_call_id"]
                for call in message.approvals
                if "approved" not in call
            }
            if not expected or set(decisions) != expected:
                raise SanadNothingToApprove()
            message.approvals = [
                {**call, "approved": decisions[call["tool_call_id"]]}
                if call["tool_call_id"] in decisions
                else call
                for call in message.approvals
            ]
            message.status = SanadMessageStatus.PENDING
            message.save(update_fields=["approvals", "status", "updated_on"])
            self._queue(message, decisions)
        return message

    def _queue(self, message: SanadMessage, decisions=None) -> None:
        from arabase.sanad.runner import start_turn

        transaction.on_commit(
            lambda: start_turn(message.id, decisions)  # noqa: B023
        )

    def run(self, message_id: int, decisions: Optional[dict] = None) -> None:
        """The background side: run the model and store what it did and said."""

        from arabase.sanad.agent import build_ai_model, run_turn
        from arabase.sanad.tools import SanadEndpoint

        message = SanadMessage.objects.select_related(
            "chat__user", "chat__workspace"
        ).get(id=message_id)
        if message.status != SanadMessageStatus.PENDING:
            return
        chat = message.chat

        def on_action(action: dict) -> None:
            # Saved as each tool finishes, so the panel can show progress.
            message.actions = [*message.actions, action]
            message.save(update_fields=["actions", "updated_on"])

        user_prompt = None
        if decisions is None:
            from arabase.sanad.agent import build_user_prompt

            question = chat.messages.filter(
                role=SanadMessageRole.USER, id__lt=message.id
            ).last()
            user_prompt = build_user_prompt(question.content, question.context)

        try:
            self.check_access(chat.user, chat.workspace)
            result = run_turn(
                model=build_ai_model(chat.model, chat.workspace),
                endpoint=SanadEndpoint(user=chat.user, workspace=chat.workspace),
                history=chat.history,
                on_action=on_action,
                user_prompt=user_prompt,
                decisions=decisions,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the chat
            logger.exception("Sanad turn %s failed", message.id)
            message.status = SanadMessageStatus.ERROR
            message.error = _turn_error(exc)
            message.save(update_fields=["status", "error", "updated_on"])
            return

        chat.history = result.history
        chat.save(update_fields=["history", "updated_on"])
        message.content = _join(message.content, result.text)
        decided = [call for call in message.approvals if "approved" in call]
        message.approvals = decided + result.approvals
        message.status = (
            SanadMessageStatus.AWAITING_APPROVAL
            if result.approvals
            else SanadMessageStatus.DONE
        )
        message.save(update_fields=["status", "content", "approvals", "updated_on"])


def _join(first: str, second: str) -> str:
    return "\n\n".join(part for part in (first, second) if part)


def _turn_error(exc: Exception) -> str:
    from pydantic_ai.exceptions import UsageLimitExceeded

    if isinstance(exc, UsageLimitExceeded):
        return "SANAD_ERROR_TOO_MANY_STEPS"
    if isinstance(exc, SanadNotAllowed):
        return "SANAD_ERROR_NOT_ALLOWED"
    if isinstance(exc, SanadTurnTooLong):
        return "SANAD_ERROR_TIMED_OUT"
    return "SANAD_ERROR_MODEL_FAILED"
