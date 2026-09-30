"""Adding, reading and removing the dashboards on a user's "My dashboards" page.

Every read is checked again at the moment it happens, so the page never shows
more than the user could open elsewhere:

- ``workspace``: the user's own permissions, as inside the workspace.
- ``link``: what the link's visitors see, while the link still exists and its
  password hash is the one the user was let in with.
- ``remote``: whatever the other server answers for the link.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Max

from arabase.dashboard.share.exceptions import DashboardShareDoesNotExist
from arabase.dashboard.share.handler import DashboardShareHandler
from arabase.dashboard.share.models import DashboardShare
from arabase.saved_dashboards.exceptions import (
    SavedDashboardDoesNotExist,
    SavedDashboardHasNoPassword,
    SavedDashboardPasswordIncorrect,
    SavedDashboardPasswordRequired,
    SavedDashboardUnavailable,
    SavedDashboardUnreachable,
)
from arabase.saved_dashboards.links import DashboardLink, parse_dashboard_link
from arabase.saved_dashboards.models import SavedDashboard, SavedDashboardSource
from arabase.saved_dashboards.remote import RemoteDashboardClient
from arabase.sealing import Sealer
from jadawel.contrib.dashboard.models import Dashboard
from jadawel.core.exceptions import ApplicationDoesNotExist
from jadawel.core.handler import CoreHandler
from jadawel.core.models import Workspace
from jadawel.core.operations import (
    ListApplicationsWorkspaceOperationType,
    ReadApplicationOperationType,
)

PASSWORD_SEALER = Sealer("arabase.saved_dashboards", "remote-link-password")

MAX_PREVIEW_WIDGETS = 24


class Status:
    OK = "ok"
    PASSWORD = "password"  # noqa: S105 - a status name, not a password
    UNAVAILABLE = "unavailable"
    UNREACHABLE = "unreachable"


REMOTE_PROBLEMS = {
    SavedDashboardPasswordRequired: Status.PASSWORD,
    SavedDashboardPasswordIncorrect: Status.PASSWORD,
    SavedDashboardUnavailable: Status.UNAVAILABLE,
    SavedDashboardUnreachable: Status.UNREACHABLE,
}


@dataclass
class SavedDashboardState:
    saved: SavedDashboard
    status: str
    source_name: str
    """The workspace's name, the other server's host, or empty for a link."""


def preview_of(widgets: list) -> list[dict]:
    """The layout a card sketches: each widget's type and size, no data."""

    return [
        {
            "type": str(widget.get("type", "")),
            "width": widget.get("width"),
            "height": widget.get("height"),
        }
        for widget in widgets[:MAX_PREVIEW_WIDGETS]
        if isinstance(widget, dict)
    ]


class SavedDashboardHandler:
    # ------------------------------------------------------------------ reading

    def get(self, user: AbstractUser, saved_id: int) -> SavedDashboard:
        """
        :raises SavedDashboardDoesNotExist: for a missing or foreign id.
        """

        try:
            return SavedDashboard.objects.select_related(
                "dashboard", "dashboard__workspace"
            ).get(id=saved_id, user=user)
        except SavedDashboard.DoesNotExist as exc:
            raise SavedDashboardDoesNotExist() from exc

    def list(self, user: AbstractUser) -> list[SavedDashboardState]:
        """Every saved dashboard with whether it can be opened now."""

        return [
            self.state(user, saved)
            for saved in SavedDashboard.objects.filter(user=user).select_related(
                "dashboard", "dashboard__workspace"
            )
        ]

    def state(self, user: AbstractUser, saved: SavedDashboard) -> SavedDashboardState:
        """Whether ``saved`` can be opened now, and where it comes from.

        Nothing is fetched from other servers: their state is the one the last
        request left (``SavedDashboard.problem``).
        """

        status, source_name = Status.OK, ""
        try:
            if saved.source == SavedDashboardSource.WORKSPACE:
                source_name = saved.dashboard.workspace.name
                saved.title = self.get_workspace_dashboard(user, saved).name
            elif saved.source == SavedDashboardSource.LINK:
                saved.title = self.get_link_share(saved).dashboard.name
            else:
                source_name = saved.origin.split("://", 1)[-1]
                status = saved.problem or Status.OK
        except SavedDashboardPasswordRequired:
            status = Status.PASSWORD
        except SavedDashboardUnavailable:
            status = Status.UNAVAILABLE
        return SavedDashboardState(saved, status, source_name)

    def saved_workspace_dashboard_ids(self, user: AbstractUser) -> set[int]:
        return set(
            SavedDashboard.objects.filter(
                user=user, source=SavedDashboardSource.WORKSPACE
            ).values_list("dashboard_id", flat=True)
        )

    def get_workspace_dashboard(
        self, user: AbstractUser, saved: SavedDashboard
    ) -> Dashboard:
        """
        :raises SavedDashboardUnavailable: when the dashboard or its workspace is
            trashed, or the user may no longer read it.
        """

        dashboard = saved.dashboard
        if dashboard is None or dashboard.trashed or dashboard.workspace.trashed:
            raise SavedDashboardUnavailable()
        if not CoreHandler().check_permissions(
            user,
            ReadApplicationOperationType.type,
            workspace=dashboard.workspace,
            context=dashboard,
            raise_permission_exceptions=False,
        ):
            raise SavedDashboardUnavailable()
        return dashboard

    def get_link_share(self, saved: SavedDashboard) -> DashboardShare:
        """The link's share, while the user is still let in.

        :raises SavedDashboardUnavailable: when the link was revoked or rotated,
            or its dashboard is gone.
        :raises SavedDashboardPasswordRequired: when the password changed, or
            one was added, since the user was let in.
        """

        try:
            share = DashboardShareHandler().get_share_by_slug(saved.slug)
        except DashboardShareDoesNotExist as exc:
            raise SavedDashboardUnavailable() from exc
        if share.public_view_password != saved.granted_password:
            raise SavedDashboardPasswordRequired()
        return share

    def call_remote(
        self,
        saved: SavedDashboard,
        call: Callable[[RemoteDashboardClient, str], Any],
    ) -> Any:
        """Runs ``call(client, token)`` against the other server.

        An expired or refused token is renewed once with the sealed password,
        so the user is asked again only when the owner changed it. Whatever
        happens is recorded in ``problem`` for the page's cards.
        """

        client = RemoteDashboardClient(saved.origin, saved.slug)
        token = saved.remote_token
        try:
            try:
                result = call(client, token)
            except SavedDashboardPasswordRequired:
                password = (
                    PASSWORD_SEALER.unseal(saved.password_sealed)
                    if saved.password_sealed
                    else None
                )
                if not password:
                    raise
                token = client.authenticate(password)
                result = call(client, token)
        except tuple(REMOTE_PROBLEMS) as exc:
            self._record_remote(saved, REMOTE_PROBLEMS[type(exc)], saved.remote_token)
            if isinstance(exc, SavedDashboardPasswordIncorrect):
                raise SavedDashboardPasswordRequired() from exc
            raise
        self._record_remote(saved, "", token)
        return result

    def _record_remote(self, saved: SavedDashboard, problem: str, token: str):
        if saved.problem != problem or saved.remote_token != token:
            saved.problem, saved.remote_token = problem, token
            saved.save(update_fields=["problem", "remote_token", "updated_on"])

    def remember(self, saved: SavedDashboard, payload: dict) -> None:
        """Keeps the name and layout the cards show, when they changed."""

        title = str((payload.get("dashboard") or {}).get("name") or "")[:255]
        preview = preview_of(payload.get("widgets") or [])
        if saved.title != title or saved.preview != preview:
            saved.title, saved.preview = title, preview
            saved.save(update_fields=["title", "preview", "updated_on"])

    def remember_dashboard(self, saved: SavedDashboard, dashboard: Dashboard):
        """``remember`` for a dashboard of this server, read from its models."""

        from jadawel.contrib.dashboard.widgets.handler import WidgetHandler
        from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

        widgets = [
            {
                "type": widget_type_registry.get_by_model(widget).type,
                "width": widget.width,
                "height": widget.height,
            }
            for widget in WidgetHandler().get_widgets(dashboard)
        ]
        self.remember(
            saved, {"dashboard": {"name": dashboard.name}, "widgets": widgets}
        )

    def list_available(self, user: AbstractUser) -> list[tuple[Workspace, list]]:
        """The dashboards of every workspace the user may list, by workspace."""

        dashboards = {}
        for dashboard in (
            Dashboard.objects.filter(
                workspace__workspaceuser__user=user,
                workspace__trashed=False,
            )
            .select_related("workspace")
            .order_by("workspace__name", "workspace_id", "order", "id")
        ):
            dashboards.setdefault(dashboard.workspace, []).append(dashboard)
        available = []
        for workspace, candidates in dashboards.items():
            allowed = set(
                CoreHandler()
                .filter_queryset(
                    user,
                    ListApplicationsWorkspaceOperationType.type,
                    Dashboard.objects.filter(id__in=[d.id for d in candidates]),
                    workspace=workspace,
                )
                .values_list("id", flat=True)
            )
            visible = [d for d in candidates if d.id in allowed]
            if visible:
                available.append((workspace, visible))
        return available

    # ------------------------------------------------------------------ changing

    def add_from_workspace(self, user: AbstractUser, dashboard_id: int):
        """
        :raises ApplicationDoesNotExist: for a missing id or another type.
        :raises UserNotInWorkspace, PermissionDenied: without read access.
        """

        application = CoreHandler().get_application(dashboard_id)
        dashboard = application.specific
        if not isinstance(dashboard, Dashboard):
            raise ApplicationDoesNotExist(f"Dashboard {dashboard_id} not found.")
        CoreHandler().check_permissions(
            user,
            ReadApplicationOperationType.type,
            workspace=dashboard.workspace,
            context=dashboard,
        )
        with transaction.atomic():
            saved, _ = SavedDashboard.objects.get_or_create(
                user=user,
                source=SavedDashboardSource.WORKSPACE,
                dashboard=dashboard,
                defaults={"order": self._next_order(user)},
            )
        self.remember_dashboard(saved, dashboard)
        return saved

    def add_link(
        self, user: AbstractUser, url: str, password: Optional[str] = None
    ) -> SavedDashboard:
        """Adds a dashboard by its public link, here or on another server.

        :raises InvalidDashboardLink: for anything but a dashboard link.
        :raises SavedDashboardPasswordRequired: when the link needs a password
            and none was given.
        :raises SavedDashboardPasswordIncorrect: for a wrong password.
        :raises SavedDashboardUnavailable: when the link does not exist.
        :raises SavedDashboardUnreachable: when the other server cannot be read.
        """

        link = parse_dashboard_link(url)
        if link.is_local:
            return self._add_local_link(user, link, password)
        return self._add_remote_link(user, link, password)

    def _add_local_link(self, user, link: DashboardLink, password):
        try:
            share = DashboardShareHandler().get_share_by_slug(link.slug)
        except DashboardShareDoesNotExist as exc:
            raise SavedDashboardUnavailable() from exc
        self._check_link_password(share, password)
        saved = self._save_link(
            user,
            SavedDashboardSource.LINK,
            link,
            granted_password=share.public_view_password,
        )
        self.remember_dashboard(saved, share.dashboard)
        return saved

    def _add_remote_link(self, user, link: DashboardLink, password):
        client = RemoteDashboardClient(link.origin, link.slug)
        token = ""
        try:
            payload = client.info()
        except SavedDashboardPasswordRequired:
            if not password:
                raise
            token = client.authenticate(password)
            payload = client.info(token)
        saved = self._save_link(
            user,
            SavedDashboardSource.REMOTE,
            link,
            password_sealed=PASSWORD_SEALER.seal(password) if token else "",
            remote_token=token,
            problem="",
        )
        self.remember(saved, payload)
        return saved

    def _check_link_password(self, share: DashboardShare, password) -> None:
        if not share.has_password:
            return
        if not password:
            raise SavedDashboardPasswordRequired()
        if not share.check_public_password(password):
            raise SavedDashboardPasswordIncorrect()

    def _save_link(self, user, source, link: DashboardLink, **values):
        with transaction.atomic():
            saved, created = SavedDashboard.objects.select_for_update().get_or_create(
                user=user,
                source=source,
                origin=link.origin,
                slug=link.slug,
                defaults={**values, "order": self._next_order(user)},
            )
            if not created:
                for name, value in values.items():
                    setattr(saved, name, value)
                saved.save()
        return saved

    def enter_password(
        self, user: AbstractUser, saved: SavedDashboard, password: str
    ) -> SavedDashboard:
        """Lets the user in again after the owner changed the password.

        :raises SavedDashboardHasNoPassword: for a workspace dashboard.
        :raises SavedDashboardPasswordIncorrect: for a wrong password.
        :raises SavedDashboardUnavailable, SavedDashboardUnreachable: when the
            link cannot be read at all.
        """

        if saved.source == SavedDashboardSource.WORKSPACE:
            raise SavedDashboardHasNoPassword()
        if saved.source == SavedDashboardSource.LINK:
            try:
                share = DashboardShareHandler().get_share_by_slug(saved.slug)
            except DashboardShareDoesNotExist as exc:
                raise SavedDashboardUnavailable() from exc
            self._check_link_password(share, password)
            saved.granted_password = share.public_view_password
            saved.save(update_fields=["granted_password", "updated_on"])
            return saved
        client = RemoteDashboardClient(saved.origin, saved.slug)
        try:
            token = client.authenticate(password)
        except (SavedDashboardUnavailable, SavedDashboardUnreachable) as exc:
            self._record_remote(saved, REMOTE_PROBLEMS[type(exc)], saved.remote_token)
            raise
        saved.password_sealed = PASSWORD_SEALER.seal(password)
        saved.save(update_fields=["password_sealed", "updated_on"])
        self._record_remote(saved, "", token)
        return saved

    def remove(self, user: AbstractUser, saved_id: int) -> None:
        self.get(user, saved_id).delete()

    def order(self, user: AbstractUser, saved_ids: list[int]) -> None:
        """Puts the user's saved dashboards in this order; others keep theirs
        after them, and ids that are not the user's are ignored."""

        position = {saved_id: index for index, saved_id in enumerate(saved_ids)}
        saved = list(SavedDashboard.objects.filter(user=user))
        saved.sort(key=lambda item: (position.get(item.id, len(position)), item.order))
        for index, item in enumerate(saved):
            item.order = index
        SavedDashboard.objects.bulk_update(saved, ["order"])

    def _next_order(self, user: AbstractUser) -> int:
        highest = SavedDashboard.objects.filter(user=user).aggregate(Max("order"))
        return (highest["order__max"] or 0) + 1
