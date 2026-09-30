"""Reading the dashboard link a user pastes."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from django.conf import settings

from arabase.saved_dashboards.exceptions import InvalidDashboardLink

# The web frontend's route for a shared dashboard, and its password page.
PUBLIC_PATH = re.compile(r"^/public/dashboard/(?P<slug>[-\w]{1,128})(?:/auth)?/?$")


@dataclass(frozen=True)
class DashboardLink:
    slug: str
    origin: str = ""
    """Empty for a link on this server, else ``scheme://host[:port]``."""

    @property
    def is_local(self) -> bool:
        return not self.origin


def _origin(url: str) -> str:
    parsed = urlparse(url or "")
    if not parsed.scheme or not parsed.hostname:
        return ""
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


def local_origins() -> set[str]:
    """Every address this server's own links are published under."""

    return {
        origin
        for origin in (
            _origin(settings.PUBLIC_WEB_FRONTEND_URL),
            _origin(settings.JADAWEL_EMBEDDED_SHARE_URL),
            _origin(settings.PUBLIC_BACKEND_URL),
        )
        if origin
    }


def parse_dashboard_link(url: str) -> DashboardLink:
    """
    :raises InvalidDashboardLink: for anything but a `/public/dashboard/<slug>`
        link. Another server's link must be https, since its password travels
        with it; plain http is accepted only where webhooks may reach private
        addresses too (development).
    """

    try:
        parsed = urlparse(url.strip())
        origin = _origin(url.strip())
    except ValueError as exc:  # an invalid port
        raise InvalidDashboardLink() from exc
    match = PUBLIC_PATH.match(parsed.path)
    if parsed.scheme not in ("http", "https") or not origin or not match:
        raise InvalidDashboardLink()
    slug = match.group("slug")
    if origin in local_origins():
        return DashboardLink(slug=slug)
    if parsed.scheme != "https" and not settings.JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS:
        raise InvalidDashboardLink()
    return DashboardLink(slug=slug, origin=origin)
