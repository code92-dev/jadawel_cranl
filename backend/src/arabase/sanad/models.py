"""Sanad (سند), the in-app AI assistant — docs/SANAD_AI_ASSISTANT.md.

A chat belongs to one user in one workspace, like upstream's enterprise
assistant. The model-facing conversation (every request, tool call and tool
result) is kept verbatim in ``SanadChat.history`` so a follow-up turn, or an
approval of a paused destructive action, resumes exactly where the model left
off. ``SanadMessage`` is the human-facing transcript the panel renders.
"""

from django.conf import settings
from django.db import models

from jadawel.core.mixins import CreatedAndUpdatedOnMixin
from jadawel.core.models import Workspace


class SanadChat(CreatedAndUpdatedOnMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="+",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    model = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="`<provider type>/<model name>` used for the last turn.",
    )
    history = models.JSONField(
        default=list,
        help_text="The pydantic-ai message history, in its JSON form.",
    )

    class Meta:
        ordering = ("-updated_on", "-id")


class SanadMessageRole(models.TextChoices):
    USER = "user"
    ASSISTANT = "assistant"


class SanadMessageStatus(models.TextChoices):
    PENDING = "pending"
    """Queued or running in a Celery worker."""
    AWAITING_APPROVAL = "awaiting_approval"
    """The model asked for a destructive action; nothing ran yet."""
    DONE = "done"
    ERROR = "error"


class SanadMessage(models.Model):
    chat = models.ForeignKey(
        SanadChat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=SanadMessageRole.choices)
    status = models.CharField(
        max_length=32,
        choices=SanadMessageStatus.choices,
        default=SanadMessageStatus.DONE,
    )
    content = models.TextField(blank=True, default="")
    context = models.JSONField(
        default=dict,
        help_text="What the user was looking at: `table_id`, `view_id`.",
    )
    actions = models.JSONField(
        default=list,
        help_text="Every tool Sanad called while producing this message.",
    )
    approvals = models.JSONField(
        default=list,
        help_text=(
            "Destructive tool calls the model asked for. Each gets an "
            "`approved` key once the user decides."
        ),
    )
    error = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="A stable error code the panel translates.",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)
