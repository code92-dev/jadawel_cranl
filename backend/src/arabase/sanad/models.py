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


class SanadBudget(CreatedAndUpdatedOnMixin, models.Model):
    """A workspace's monthly allowance for Sanad.

    A limit left empty falls back to the instance default
    (``JADAWEL_SANAD_MONTHLY_TURN_LIMIT`` / ``_TOKEN_LIMIT``); with neither set,
    that dimension is unlimited. See ``arabase.sanad.budget``.
    """

    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.CASCADE,
        related_name="+",
    )
    monthly_turn_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Messages Sanad may answer per calendar month (UTC).",
    )
    monthly_token_limit = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Model tokens, input plus output, per calendar month (UTC).",
    )


class SanadUsage(models.Model):
    """What Sanad used in one workspace during one calendar month (UTC)."""

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="+",
    )
    month = models.DateField(help_text="The first day of the month.")
    turns = models.PositiveIntegerField(
        default=0, help_text="Messages sent to Sanad (an approval is not one)."
    )
    requests = models.PositiveIntegerField(default=0)
    input_tokens = models.PositiveBigIntegerField(default=0)
    output_tokens = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "month"], name="arabase_sanad_usage_month"
            )
        ]

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens
