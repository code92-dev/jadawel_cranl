"""The dashboards a user collected on their "My dashboards" page (لوحاتي).

docs/MY_DASHBOARDS.md. A row points at the dashboard in one of three ways, and
nothing about the dashboard itself is copied except what the page's cards show
while it cannot be reached (``title``, ``preview``).
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from jadawel.contrib.dashboard.models import Dashboard
from jadawel.core.mixins import CreatedAndUpdatedOnMixin


class SavedDashboardSource(models.TextChoices):
    WORKSPACE = "workspace"
    """A dashboard of one of the user's workspaces, read with their permissions."""
    LINK = "link"
    """A public link on this server, read as the link's visitors read it."""
    REMOTE = "remote"
    """A public link on another Jadawel server, fetched through this one."""


class SavedDashboard(CreatedAndUpdatedOnMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    source = models.CharField(max_length=16, choices=SavedDashboardSource.choices)
    order = models.PositiveIntegerField(default=0)
    dashboard = models.ForeignKey(
        Dashboard,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="`workspace` only.",
    )
    origin = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="`remote` only: the other server, as `https://host[:port]`.",
    )
    slug = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="`link` and `remote`: the slug of the public link.",
    )
    granted_password = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text=(
            "`link` only: the link's password hash when the user was let in. "
            "Access lasts while it still matches, so changing the password or "
            "adding one asks the user again. Never the password itself."
        ),
    )
    password_sealed = models.TextField(
        blank=True,
        default="",
        help_text=(
            "`remote` only: the password, sealed (`arabase.sealing`), to get a "
            "new token when the other server's expires."
        ),
    )
    remote_token = models.TextField(
        blank=True,
        default="",
        help_text="`remote` only: the other server's current access token.",
    )
    title = models.CharField(
        max_length=255, blank=True, default="", help_text="The last known name."
    )
    preview = models.JSONField(
        default=list,
        blank=True,
        help_text="The last known layout: `[{type, width, height}]` per widget.",
    )
    problem = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text=(
            "`remote` only: why the last request failed "
            "(`password`, `unavailable`, `unreachable`); empty once it works."
        ),
    )

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "dashboard"],
                condition=Q(source="workspace"),
                name="arabase_saved_dashboard_workspace_once",
            ),
            models.UniqueConstraint(
                fields=["user", "origin", "slug"],
                condition=Q(source__in=["link", "remote"]),
                name="arabase_saved_dashboard_link_once",
            ),
        ]
