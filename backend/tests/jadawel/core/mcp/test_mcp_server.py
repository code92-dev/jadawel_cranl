import json
from uuid import UUID

from django.db import transaction

import pytest
from asgiref.sync import async_to_sync
from loguru import logger
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from jadawel.core.mcp import JadawelMCPServer, current_key
from jadawel.core.mcp.errors import (
    SAFE_MCP_ERROR_MESSAGES,
    MCPErrorCode,
    SafeMCPToolError,
)
from jadawel.core.mcp.registries import MCPTool, mcp_tool_registry


class FailingMCPTool(MCPTool):
    type = "test_failing_tool"

    def _sync_call(self, endpoint, args):
        raise RuntimeError("PROTECTED-CANARY-VALUE")


class ProtectionUnavailableMCPTool(MCPTool):
    type = "list_table_rows"

    def _sync_call(self, endpoint, args):
        raise SafeMCPToolError(
            MCPErrorCode.PROTECTION_UNAVAILABLE,
            retryable=False,
        )


@pytest.mark.django_db
def test_create_server():
    async def inner():
        mcp = JadawelMCPServer()
        assert mcp._mcp_server.name == "Jadawel MCP"
        assert "Jadawel" in mcp._mcp_server.instructions

    with transaction.atomic():
        async_to_sync(inner)()


@pytest.mark.django_db
def test_get_endpoint_invalid_key(data_fixture):
    mcp = JadawelMCPServer()

    key_token = current_key.set("test-key")

    try:

        async def inner():
            endpoint = await mcp.get_endpoint()
            assert endpoint is None

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_get_endpoint_user_not_part_of_workspace(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)

    mcp = JadawelMCPServer()

    key_token = current_key.set(endpoint.key)

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                endpoint = await mcp.get_endpoint()
            assert endpoint is None

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_get_valid_endpoint(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)

    mcp = JadawelMCPServer()

    key_token = current_key.set(endpoint.key)

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                endpoint = await mcp.get_endpoint()
                assert endpoint.id == endpoint.id

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_list_tools_without_endpoint_key(data_fixture):
    mcp = JadawelMCPServer()
    key_token = current_key.set("test-key")

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                # Because the endpoint key is invalid, it should not respond with any
                # tools.
                tools = await client.list_tools()
                assert len(tools.tools) == 0

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_list_tools_with_valid_endpoint_key(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                # Because the endpoint key is invalid, it should not respond with any
                # tools.
                tools = await client.list_tools()
                assert len(tools.tools) > 0

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_call_tool_without_endpoint_key(data_fixture):
    mcp = JadawelMCPServer()

    key_token = current_key.set("test-key")

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                result = await client.call_tool("list_tables", {})
                assert result.isError is True
                error = json.loads(result.content[0].text)["error"]
                assert error["code"] == "MCP_ACCESS_DENIED"
                assert error["retryable"] is False
                UUID(error["correlation_id"])
                assert "endpoint" not in result.content[0].text.lower()

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


@pytest.mark.django_db
def test_call_tool_returns_a_content_blind_protocol_error(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)
    captured_logs = []
    sink_id = logger.add(captured_logs.append, format="{message}")
    tool = FailingMCPTool()
    mcp_tool_registry.register(tool)

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                result = await client.call_tool(tool.type, {})
                assert result.isError is True
                error = json.loads(result.content[0].text)["error"]
                assert error["code"] == "MCP_TOOL_FAILED"
                assert error["retryable"] is False
                UUID(error["correlation_id"])
                assert set(error) == {"code", "correlation_id", "message", "retryable"}
                assert error["message"] == SAFE_MCP_ERROR_MESSAGES[error["code"]]
                assert "PROTECTED-CANARY-VALUE" not in result.content[0].text

        with transaction.atomic():
            async_to_sync(inner)()

        assert "PROTECTED-CANARY-VALUE" not in "".join(captured_logs)
    finally:
        mcp_tool_registry.unregister(tool)
        logger.remove(sink_id)
        current_key.reset(key_token)


@pytest.mark.django_db
def test_call_tool_validation_error_does_not_echo_arguments(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)
    argument_canary = "PROTECTED-ARGUMENT-CANARY"
    captured_logs = []
    sink_id = logger.add(captured_logs.append, format="{message}")

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                result = await client.call_tool(
                    "list_table_rows", {"table_id": argument_canary}
                )
                assert result.isError is True
                error = json.loads(result.content[0].text)["error"]
                assert error["code"] == "MCP_TOOL_FAILED"
                assert error["retryable"] is False
                UUID(error["correlation_id"])
                assert set(error) == {"code", "correlation_id", "message", "retryable"}
                assert error["message"] == SAFE_MCP_ERROR_MESSAGES[error["code"]]
                assert argument_canary not in result.content[0].text

        with transaction.atomic():
            async_to_sync(inner)()

        assert argument_canary not in "".join(captured_logs)
    finally:
        logger.remove(sink_id)
        current_key.reset(key_token)


@pytest.mark.django_db
def test_call_tool_returns_allowlisted_protection_error(data_fixture, monkeypatch):
    endpoint = data_fixture.create_mcp_endpoint()
    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)
    tool = ProtectionUnavailableMCPTool()
    monkeypatch.setattr(mcp_tool_registry, "match_by_name", lambda name: tool)

    try:

        async def inner():
            result = await mcp.call_tool(tool.type, {})
            assert result.isError is True
            error = json.loads(result.content[0].text)["error"]
            assert error["code"] == "PROTECTION_UNAVAILABLE"
            assert error["retryable"] is False
            UUID(error["correlation_id"])
            assert set(error) == {"code", "correlation_id", "message", "retryable"}
            assert error["message"] == SAFE_MCP_ERROR_MESSAGES[error["code"]]

        with transaction.atomic():
            async_to_sync(inner)()
    finally:
        current_key.reset(key_token)
