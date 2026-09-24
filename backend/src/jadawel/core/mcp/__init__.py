import contextvars
import json
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from asgiref.sync import sync_to_async
from loguru import logger

from jadawel.core.mcp.errors import (
    SAFE_MCP_ERROR_MESSAGES,
    MCPErrorCode,
    SafeMCPToolError,
)
from jadawel.core.mcp.sse import DjangoChannelsSseServerTransport

if TYPE_CHECKING:
    from mcp.types import Tool
    from starlette.applications import Starlette

current_key: contextvars.ContextVar[str] = contextvars.ContextVar("current_key")


def _safe_tool_error(code: MCPErrorCode, *, retryable: bool, correlation_id: UUID):
    from mcp.types import CallToolResult, TextContent

    payload = {
        "error": {
            "code": code,
            "correlation_id": str(correlation_id),
            "message": SAFE_MCP_ERROR_MESSAGES[code],
            "retryable": retryable,
        }
    }
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(payload, separators=(",", ":"), sort_keys=True),
            )
        ],
        isError=True,
    )


class JadawelMCPServer:
    """
    This class is inspired by FastMCP
    (https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/fastmcp/server.py)
    but modified to work better in combination with Django Rest Framework that Jadawel
    uses.

    The MCP server can be tested with tools like:

    SERVER_PORT=3001 npx @modelcontextprotocol/inspector
    npx @wong2/mcp-cli --sse URL
    """

    def __init__(self):
        from mcp.server.lowlevel.server import Server
        from mcp.server.lowlevel.server import lifespan as default_lifespan

        self._mcp_server = Server(
            name="Jadawel MCP",
            instructions="Handles all the actions, operations, mutations, and tools "
            "related to Jadawel.",
            lifespan=default_lifespan,
        )

        self._setup_handlers()

    def _setup_handlers(self):
        self._mcp_server.list_tools()(self.list_tools)
        # The SDK's JSON Schema validator formats the rejected input value into
        # its caller-visible error before our handler runs. Validate with each
        # tool's Pydantic schema inside ``call_tool`` instead, where every
        # exception is converted to a fixed, content-blind protocol error.
        self._mcp_server.call_tool(validate_input=False)(self.call_tool)

        # Return an empty list because there are no resources, prompts, and
        # resource_templates in Jadawel.
        self._mcp_server.list_resources()(self.return_empty)
        self._mcp_server.list_prompts()(self.return_empty)
        self._mcp_server.list_resource_templates()(self.return_empty)

    async def return_empty(self) -> list:
        """
        Placeholder so that the server always responds with an empty list when certain
        resources are requested.
        """

        return []

    async def get_endpoint(self):
        from jadawel.core.mcp.models import MCPEndpoint
        from jadawel.core.subjects import UserSubjectType

        key = current_key.get()
        try:
            endpoint = await MCPEndpoint.objects.select_related(
                "user", "user__profile", "workspace"
            ).aget(key=key)
            # This call checks if the user is active, account is not deleted, and if it
            # belongs in the workspace. It's important to check this everytime an
            # operation is done because the permissions could have changed.
            check_method = UserSubjectType().is_in_workspace
            valid = await sync_to_async(check_method)(endpoint.user, endpoint.workspace)
            if not valid:
                return None
            return endpoint
        except MCPEndpoint.DoesNotExist:
            return None

    async def call_tool(self, name: str, arguments):
        from jadawel.core.mcp.registries import mcp_tool_registry

        endpoint = await self.get_endpoint()
        if not endpoint:
            return _safe_tool_error(
                MCPErrorCode.ACCESS_DENIED,
                retryable=False,
                correlation_id=uuid4(),
            )
        tool = mcp_tool_registry.match_by_name(name)
        # `enabled` has to be checked here and not only in `list_tools`: a client
        # is free to skip `tools/list` and call a name it already knows, so
        # filtering the listing alone leaves every disabled tool reachable. The
        # answer is deliberately the same as for an unknown name — whether a tool
        # exists but is switched off is not information a caller needs.
        if not tool or not tool.enabled:
            return _safe_tool_error(
                MCPErrorCode.TOOL_NOT_FOUND,
                retryable=False,
                correlation_id=uuid4(),
            )
        try:
            return await tool.call(endpoint, arguments)
        except SafeMCPToolError as exc:
            correlation_id = uuid4()
            logger.bind(
                correlation_id=str(correlation_id),
                tool=name,
                outcome="error",
                safe_reason=exc.code.value,
            ).error("MCP tool call rejected")
            return _safe_tool_error(
                exc.code,
                retryable=exc.retryable,
                correlation_id=correlation_id,
            )
        except Exception:
            correlation_id = uuid4()
            logger.bind(
                correlation_id=str(correlation_id),
                tool=name,
                outcome="error",
                safe_reason="MCP_TOOL_FAILED",
            ).error("MCP tool call failed")
            return _safe_tool_error(
                MCPErrorCode.TOOL_FAILED,
                retryable=False,
                correlation_id=correlation_id,
            )

    async def list_tools(self) -> list["Tool"]:
        from jadawel.core.mcp.registries import mcp_tool_registry

        endpoint = await self.get_endpoint()
        if not endpoint:
            # It's only possible to respond with a list of `MCPTool` objects. If the
            # user isn't active anymore, then we can respond with an empty list,
            # insinuating that nothing is possible anymore.
            return []
        return await mcp_tool_registry.list_all_tools(endpoint)

    def sse_app(self) -> "Starlette":
        """
        Returns an ASGI application that can handle MCP SSE connections.

        return: Starlette: The ASGI application for handling MCP SSE connections.
        """

        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse_path = "/mcp/{key}/sse"
        messages_path = "/mcp/messages/"
        sse = DjangoChannelsSseServerTransport(messages_path)

        async def handle_sse(request: Request) -> None:
            key = request.path_params["key"]
            key_ctx = current_key.set(key)

            endpoint = await self.get_endpoint()
            if not endpoint:
                # If there is no endpoint, then there is no need to start a
                # connection. It's valid to immediately respond with a 401 error.
                return Response("Endpoint not found.", status_code=401)

            try:
                async with sse.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,  # type: ignore[reportPrivateUsage]
                ) as streams:
                    await self._mcp_server.run(
                        streams[0],
                        streams[1],
                        self._mcp_server.create_initialization_options(),
                    )
                return Response()
            except Exception as exc:
                # This is a known issue in FastMCP
                # (https://github.com/jlowin/fastmcp/issues/671) that is not causing any
                # critical issues in practice, but it does cause some noise in the logs.
                if isinstance(
                    exc, RuntimeError
                ) and "after response already completed" in str(exc):
                    return Response(status_code=204)

                logger.error("MCP SSE connection failed")
                return Response("MCP server error", status_code=500)
            finally:
                # Reset the context variable when done
                current_key.reset(key_ctx)

        # It might seem a bit hacky to use Starlette here instead of the existing
        # Django logic. However, it made more sense to stay as close to the recommended
        # code of the MCP library
        # https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#mounting-to-an-existing-asgi-server
        # for compatibility reasons. If anything changes in the Python SDK, which seems
        # to be active development, then we should remain close in terms of
        # compatibility.
        return Starlette(
            debug=False,
            routes=[
                Route(sse_path, endpoint=handle_sse),
                Mount(messages_path, app=sse.handle_post_message),
            ],
        )


_jadawel_mcp = None


def get_jadawel_mcp_server() -> JadawelMCPServer:
    global _jadawel_mcp
    if _jadawel_mcp is None:
        _jadawel_mcp = JadawelMCPServer()
    return _jadawel_mcp
