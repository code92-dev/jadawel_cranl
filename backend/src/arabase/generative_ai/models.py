"""Instance-wide AI provider settings managed by administrators.

One row per provider. Core resolves a provider's settings in this order: an
explicit override (an AI integration's own settings), the workspace, these
rows, then the ``JADAWEL_<PROVIDER>_*`` environment variables. API keys are
stored sealed (``arabase.generative_ai.store``), never in plain text.
"""

from django.conf import settings
from django.db import models

from jadawel.core.mixins import CreatedAndUpdatedOnMixin


class GenerativeAIProviderSettings(CreatedAndUpdatedOnMixin, models.Model):
    provider = models.CharField(
        max_length=32,
        unique=True,
        help_text="The core generative AI model type, e.g. `openai`.",
    )
    api_key_sealed = models.TextField(
        blank=True,
        default="",
        help_text="The API key, encrypted with a key derived from SECRET_KEY.",
    )
    api_key_hint = models.CharField(
        max_length=8,
        blank=True,
        default="",
        help_text="The key's last characters, shown so admins can recognise it.",
    )
    enabled_models = models.JSONField(default=list, help_text="Enabled model names.")
    host = models.CharField(
        max_length=500, blank=True, default="", help_text="Ollama only."
    )
    base_url = models.CharField(
        max_length=500, blank=True, default="", help_text="OpenAI only, optional."
    )
    organization = models.CharField(max_length=255, blank=True, default="")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ("provider",)
