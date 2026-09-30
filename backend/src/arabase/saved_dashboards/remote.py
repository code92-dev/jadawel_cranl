"""Reading a dashboard shared on another Jadawel server.

This server calls the other one's anonymous public-dashboard API
(``/api/arabase/public/dashboard/<slug>/``) on the user's behalf, exactly as a
visitor's browser would, so the other server needs nothing new and its owner's
password, link rotation and revocation keep working.

Requests go through the webhook request function, so the operator's rules for
reaching the outside world apply here too: private and internal addresses are
refused unless ``JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS`` is set, and the IP and
hostname block lists hold. Redirects are not followed, since they could lead
anywhere.
"""

import json
from typing import Any, Optional
from urllib.parse import quote

from django.conf import settings

from arabase.saved_dashboards.exceptions import (
    RemoteDispatchFailed,
    SavedDashboardPasswordIncorrect,
    SavedDashboardPasswordRequired,
    SavedDashboardUnavailable,
    SavedDashboardUnreachable,
)

REQUEST_TIMEOUT = 10
"""Seconds, to connect and between bytes. A widget's data is small; a server
this slow is treated as unreachable rather than holding a web worker."""

MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class RemoteDashboardClient:
    def __init__(self, origin: str, slug: str):
        self.base_url = f"{origin}/api/arabase/public/dashboard/{quote(slug)}/"

    def info(self, token: str = "") -> dict:
        """The dashboard, its widgets and its data sources.

        :raises SavedDashboardPasswordRequired: without a valid token.
        :raises SavedDashboardUnavailable: when the link no longer exists.
        :raises SavedDashboardUnreachable: see ``_call``.
        """

        status, data = self._call("GET", "", token)
        if status == 401:
            raise SavedDashboardPasswordRequired()
        if status == 404:
            raise SavedDashboardUnavailable()
        if status != 200 or not _looks_like_dashboard(data):
            raise SavedDashboardUnreachable()
        return data

    def dispatch(self, token: str, data_source_id: int) -> Any:
        """One data source's result.

        :raises SavedDashboardPasswordRequired: without a valid token.
        :raises RemoteDispatchFailed: for any other refusal, which concerns this
            data source only.
        """

        status, data = self._call("POST", f"dispatch/{int(data_source_id)}/", token)
        if status == 401:
            raise SavedDashboardPasswordRequired()
        if status != 200:
            raise RemoteDispatchFailed()
        return data

    def authenticate(self, password: str) -> str:
        """Exchanges the password for a token.

        :raises SavedDashboardPasswordIncorrect: for a wrong password.
        :raises SavedDashboardUnavailable: when the link no longer exists.
        """

        status, data = self._call("POST", "auth/", body={"password": password})
        if status == 401:
            raise SavedDashboardPasswordIncorrect()
        if status == 404:
            raise SavedDashboardUnavailable()
        token = data.get("access_token") if isinstance(data, dict) else None
        if status != 200 or not isinstance(token, str) or not token:
            raise SavedDashboardUnreachable()
        return token

    def _call(
        self,
        method: str,
        path: str,
        token: str = "",
        body: Optional[dict] = None,
    ) -> tuple[int, Any]:
        """
        :raises SavedDashboardUnreachable: when the server cannot be reached, is
            refused by the outbound rules, or answers with something that is not
            JSON or is too large.
        """

        from jadawel.contrib.database.webhooks.validators import (
            get_webhook_request_function,
        )

        headers = {"Accept": "application/json"}
        if token:
            headers[settings.PUBLIC_VIEW_AUTHORIZATION_HEADER] = f"JWT {token}"
        try:
            response = get_webhook_request_function()(
                method,
                self.base_url + path,
                headers=headers,
                json=body if body is not None else ({} if method == "POST" else None),
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
            )
            content = b""
            for chunk in response.iter_content(chunk_size=64 * 1024):
                content += chunk
                if len(content) > MAX_RESPONSE_BYTES:
                    raise SavedDashboardUnreachable()
            response.close()
        except SavedDashboardUnreachable:
            raise
        except Exception as exc:  # noqa: BLE001 - any network or refusal error
            raise SavedDashboardUnreachable() from exc
        if response.status_code in (401, 404):
            return response.status_code, None
        try:
            return response.status_code, json.loads(content or b"null")
        except ValueError as exc:
            raise SavedDashboardUnreachable() from exc


def _looks_like_dashboard(data: Any) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("dashboard"), dict)
        and isinstance(data.get("widgets"), list)
        and isinstance(data.get("data_sources"), list)
    )
