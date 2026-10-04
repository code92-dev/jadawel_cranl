"""Who may use the features still being introduced (docs/FEATURE_ACCESS.md).

Automations, the application builder and Sanad started out limited to instance
administrators (staff). An administrator now opens each one to every user, or
to the email addresses listed for it. Staff keep every feature regardless.

A grant names an email address, not an account: it covers the account that
has that address today, and one created with it later.
"""

from django.conf import settings
from django.db import models


class Feature(models.TextChoices):
    """A gated feature. ``automation`` and ``builder`` are also the type names
    of the applications they create, which is how creation is checked."""

    AUTOMATION = "automation", "Automations"
    BUILDER = "builder", "Applications"
    SANAD = "sanad", "Sanad"


class FeatureAccess(models.Model):
    """Whether one feature is open to every user. No row means it is not."""

    feature = models.CharField(max_length=32, choices=Feature.choices, unique=True)
    everyone = models.BooleanField(
        default=False, help_text="Every user may use the feature."
    )
    updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ("feature",)


class FeatureAccessGrant(models.Model):
    """One email address that may use a feature while it is not open to all."""

    feature = models.CharField(max_length=32, choices=Feature.choices)
    email = models.CharField(
        max_length=254, help_text="Normalized like a user's email: lower case."
    )
    created_on = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ("feature", "email")
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "email"], name="arabase_feature_grant_unique"
            )
        ]
