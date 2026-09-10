import os
from datetime import timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone

import jwt
from rest_framework.request import Request

from arabase.dashboard.share.exceptions import (
    DashboardShareDoesNotExist,
    NoAuthorizationToPubliclySharedDashboard,
)
from arabase.dashboard.share.models import DashboardShare
from jadawel.contrib.dashboard.models import Dashboard

DEFAULT_TOKEN_LIFETIME_HOURS = 24 * 7


def token_lifetime() -> timedelta:
    """How long a share token stays valid after the password is entered."""

    raw = os.getenv("JADAWEL_DASHBOARD_SHARE_TOKEN_HOURS", "")
    try:
        hours = int(raw) if raw else DEFAULT_TOKEN_LIFETIME_HOURS
    except ValueError:
        hours = DEFAULT_TOKEN_LIFETIME_HOURS
    return timedelta(hours=max(hours, 1))


class DashboardShareHandler:
    """Create, rotate, protect and resolve the public link of a dashboard.

    The JWT scheme is the one
    :class:`jadawel.contrib.database.views.handler.ViewHandler` uses for password
    protected views: the secret is derived from the slug, the password hash and
    the server ``SECRET_KEY``, so rotating either the slug or the password
    invalidates every token that was handed out before.

    Tokens also expire on their own. Rotation is the only other revocation, and
    it revokes for everyone at once — which makes it useless against a single
    token that has leaked out of one visitor's browser.
    """

    TOKEN_ALGORITHM = "HS256"

    def get_share(self, dashboard: Dashboard) -> DashboardShare:
        """
        :raises DashboardShareDoesNotExist: If the dashboard is not shared.
        """

        try:
            return dashboard.share
        except DashboardShare.DoesNotExist as exc:
            raise DashboardShareDoesNotExist(
                "The dashboard is not shared publicly."
            ) from exc

    def get_share_or_none(self, dashboard: Dashboard) -> Optional[DashboardShare]:
        try:
            return self.get_share(dashboard)
        except DashboardShareDoesNotExist:
            return None

    def create_share(self, dashboard: Dashboard) -> DashboardShare:
        """Shares the dashboard, or returns the existing link if there is one."""

        share, _ = DashboardShare.objects.get_or_create(dashboard=dashboard)
        return share

    def delete_share(self, dashboard: Dashboard):
        """Revokes the public link. A no-op when the dashboard is not shared."""

        DashboardShare.objects.filter(dashboard=dashboard).delete()

    def rotate_slug(self, share: DashboardShare) -> DashboardShare:
        share.rotate_slug()
        share.save(update_fields=["slug", "updated_on"])
        return share

    def set_password(
        self, share: DashboardShare, password: Optional[str]
    ) -> DashboardShare:
        """Sets the public password, or removes it when ``password`` is empty."""

        if password:
            share.set_password(password)
        else:
            share.public_view_password = ""
        share.save(update_fields=["public_view_password", "updated_on"])
        return share

    def get_share_by_slug(self, slug: str) -> DashboardShare:
        """
        :raises DashboardShareDoesNotExist: If no live dashboard uses that slug.
        """

        try:
            share = DashboardShare.objects.select_related(
                "dashboard", "dashboard__workspace"
            ).get(slug=slug)
        except DashboardShare.DoesNotExist as exc:
            raise DashboardShareDoesNotExist(
                "The public dashboard does not exist."
            ) from exc

        dashboard = share.dashboard
        if dashboard.trashed or dashboard.workspace.trashed:
            raise DashboardShareDoesNotExist("The public dashboard does not exist.")

        # Keep dashboard share records for audit and reactivation, but stop
        # serving them while a managed organization is suspended or restricted.
        from django.apps import apps as django_apps

        if django_apps.is_installed("jadawel_organizations"):
            try:
                from jadawel_organizations.policy import public_workspace_allowed
            except ImportError:
                public_workspace_allowed = None
            if public_workspace_allowed and not public_workspace_allowed(
                dashboard.workspace
            ):
                raise DashboardShareDoesNotExist("The public dashboard does not exist.")

        return share

    def get_public_share_by_slug(
        self,
        slug: str,
        authorization_token: Optional[str] = None,
    ) -> DashboardShare:
        """
        Resolves the public link and checks the visitor may open it.

        The password applies to everyone, including members of the owning
        workspace. A shared *view* lets a member through on their session alone,
        but that makes the link untestable: the owner opens their own protected
        dashboard, is never asked, and cannot tell whether the password works.
        Members lose nothing — they still reach the dashboard at its normal
        `/dashboard/<id>` URL without a password.

        :raises DashboardShareDoesNotExist: If no live dashboard uses that slug.
        :raises NoAuthorizationToPubliclySharedDashboard: If the link is password
            protected and no valid token was provided.
        """

        share = self.get_share_by_slug(slug)

        if not share.has_password:
            return share

        if authorization_token and self.is_token_valid(share, authorization_token):
            return share

        raise NoAuthorizationToPubliclySharedDashboard(
            "The public dashboard is password protected."
        )

    def _get_jwt_secret(self, share: DashboardShare) -> str:
        return f"{share.slug}-{share.public_view_password}-{settings.SECRET_KEY}"

    def encode_token(self, share: DashboardShare) -> str:
        """Creates the token that authorizes public requests."""

        return jwt.encode(
            {
                "slug_id": share.slug,
                "exp": timezone.now() + token_lifetime(),
            },
            key=self._get_jwt_secret(share),
            algorithm=self.TOKEN_ALGORITHM,
        )

    def decode_token(self, share: DashboardShare, token: str) -> Dict[str, Any]:
        return jwt.decode(
            token,
            key=self._get_jwt_secret(share),
            algorithms=[self.TOKEN_ALGORITHM],
        )

    def is_token_valid(self, share: DashboardShare, token: str) -> bool:
        try:
            self.decode_token(share, token)
            return True
        except jwt.InvalidTokenError:
            return False


def get_public_authorization_token(request: Request) -> Optional[str]:
    """Reads the shared-link token from the ``Jadawel-View-Authorization`` header.

    The same header the database module uses for password protected views, so a
    single frontend helper covers both.
    """

    auth_header = request.headers.get(settings.PUBLIC_VIEW_AUTHORIZATION_HEADER, None)
    try:
        _, token = auth_header.split(" ", 1)
    except (AttributeError, ValueError):
        return None
    return token
