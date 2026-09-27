"""The actions Sanad can take inside a workspace, one module per domain.

Every tool is a ``SanadTool`` (``base``) and runs as the signed-in user, through
the same permission-checked services, action types and serializers the editors
use, so the assistant can never do anything the person chatting could not do by
hand. A domain module exposes ``get_tools()``; adding a tool means adding it to
its domain's list, and adding a domain means adding its module to ``DOMAINS``.
"""

from importlib import import_module

from arabase.sanad.tools.base import (
    APPROVAL_TOOLS,
    SanadEndpoint,
    SanadTool,
    safe_tool_error,
)

__all__ = [
    "APPROVAL_TOOLS",
    "DOMAINS",
    "SanadEndpoint",
    "SanadTool",
    "get_sanad_tools",
    "safe_tool_error",
]

DOMAINS = (
    "core",
    "database",
    "form",
    "automation",
    "builder",
    "builder_elements",
    "dashboard",
    "page",
)
"""Modules of this package, in the order their tools are offered."""


def get_sanad_tools() -> list[SanadTool]:
    """Every tool Sanad can call, built fresh so registry state is current."""

    tools = []
    for domain in DOMAINS:
        tools += import_module(f"{__name__}.{domain}").get_tools()
    return tools
