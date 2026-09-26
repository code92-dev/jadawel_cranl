"""The Content-Security-Policy that seals an AI-authored page in.

Computed on the backend rather than assembled in the browser so the policy is
not something a tampered frontend bundle can loosen: the API hands the finished
string to the client, which only injects it.

The policy is the *second* line of defence. The first is the iframe itself,
which is rendered with ``sandbox="allow-scripts"`` and deliberately without
``allow-same-origin``, giving the document an opaque origin with no cookies, no
localStorage, no parent DOM, no top-level navigation and no popups.
"""

import os

DEFAULT_EXTERNAL_HOSTS = [
    "https://cdn.jsdelivr.net",
    "https://unpkg.com",
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
]


def get_external_hosts() -> list[str]:
    """The CDN allowlist, overridable per deployment.

    Read from the environment at call time rather than declared in
    ``config/settings/base.py``: this is fork-only configuration, and keeping it
    out of the core settings module keeps the feature additive. Same approach as
    ``JADAWEL_DASHBOARD_SHARE_TOKEN_HOURS`` in ``arabase.dashboard.share``.
    """

    raw = os.getenv("JADAWEL_PAGE_VIEW_EXTERNAL_HOSTS", "")
    if not raw.strip():
        return list(DEFAULT_EXTERNAL_HOSTS)
    return [host.strip() for host in raw.split(",") if host.strip()]


def build_page_csp(allow_external_resources: bool = False) -> str:
    """Return the policy for a page, as a single header-style string.

    ``connect-src 'none'`` is present in **both** modes and is the load-bearing
    directive: the page is handed real row data, and it blocks fetch, XHR,
    WebSocket, EventSource and ``sendBeacon``. It does not stop the frame
    navigating itself to a URL that carries the data, and WebRTC is outside
    CSP, so it narrows the ways out rather than sealing them. What keeps that
    safe is that a page only receives rows its author can already read, plus
    protected values approved for its exact HTML.

    ``'unsafe-inline'`` and ``'unsafe-eval'`` are granted on purpose. The whole
    document is untrusted by construction, so nonces would protect nothing,
    and with the network sealed off ``eval`` buys an attacker nothing while
    buying ordinary templating libraries a great deal.
    """

    script_src = ["'unsafe-inline'", "'unsafe-eval'"]
    style_src = ["'unsafe-inline'"]
    font_src = ["data:"]
    img_src = ["data:", "blob:"]

    if allow_external_resources:
        hosts = get_external_hosts()
        script_src += hosts
        style_src += hosts
        font_src += hosts
        # The honest cost of the opt-in: an <img> pointing at an attacker's
        # host is a one-way channel out. There is no way to allow CDN assets
        # without widening img-src to something a beacon fits through, which is
        # why the toggle is off by default and warned about in the UI.
        img_src.append("https:")

    directives = [
        "default-src 'none'",
        f"script-src {' '.join(script_src)}",
        f"style-src {' '.join(style_src)}",
        f"img-src {' '.join(img_src)}",
        f"font-src {' '.join(font_src)}",
        "media-src data: blob:",
        # Never relaxed, in either mode.
        "connect-src 'none'",
        "form-action 'none'",
        "frame-src 'none'",
        "child-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
    ]
    return "; ".join(directives)
