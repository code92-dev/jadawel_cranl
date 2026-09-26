import dataclasses

from django.core.exceptions import ImproperlyConfigured

import pytest

from arabase.mcp.protection.interceptor import (
    MCPToolContract,
    get_mcp_tool_protection_contract,
    intercept_mcp_tool_call,
    validate_mcp_tool_protection_contracts,
)
from arabase.mcp.protection.policy_state import (
    MCPProtectedFieldBinding,
    MCPProtectionPolicyState,
)
from jadawel.core.action.registries import action_type_registry
from jadawel.core.mcp.errors import MCPErrorCode, SafeMCPToolError
from jadawel.core.mcp.registries import MCPTool, mcp_tool_registry


def test_every_registered_mcp_tool_uses_the_base_call_and_has_a_contract():
    for tool in mcp_tool_registry.get_all():
        assert tool.__class__.call is MCPTool.call, tool.type
        contract = get_mcp_tool_protection_contract(tool.type)
        assert isinstance(contract, MCPToolContract), tool.type


def test_arabase_registers_the_protection_interceptor():
    assert mcp_tool_registry.call_interceptor is intercept_mcp_tool_call


def test_registered_mcp_actions_never_carry_endpoint_keys():
    for action_name in ("create_mcp_endpoint", "delete_mcp_endpoint"):
        action_type = action_type_registry.get(action_name)
        param_names = {field.name for field in dataclasses.fields(action_type.Params)}

        assert "endpoint_key" not in param_names


def test_empty_policy_preserves_existing_tool_behavior(monkeypatch):
    monkeypatch.setattr(
        "arabase.mcp.protection.interceptor.get_mcp_protection_policy_state",
        lambda endpoint: MCPProtectionPolicyState(),
    )
    executed = False

    def execute():
        nonlocal executed
        executed = True
        return {"unchanged": True}

    result = intercept_mcp_tool_call(object(), _DeclaredTestTool(), {}, execute)

    assert result == {"unchanged": True}
    assert executed is True


def test_empty_policy_preserves_an_additive_tool_without_a_contract(monkeypatch):
    monkeypatch.setattr(
        "arabase.mcp.protection.interceptor.get_mcp_protection_policy_state",
        lambda endpoint: MCPProtectionPolicyState(),
    )
    executed = False

    def execute():
        nonlocal executed
        executed = True
        return {"unchanged": True}

    result = intercept_mcp_tool_call(object(), _UndeclaredTestTool(), {}, execute)

    assert result == {"unchanged": True}
    assert executed is True


def test_non_empty_policy_rejects_an_additive_tool_without_a_contract(monkeypatch):
    monkeypatch.setattr(
        "arabase.mcp.protection.interceptor.get_mcp_protection_policy_state",
        lambda endpoint: MCPProtectionPolicyState(
            protected_fields=(
                MCPProtectedFieldBinding(
                    field_id=1, table_id=1, field_name="x", field_type="text"
                ),
            )
        ),
    )
    executed = False

    def execute():
        nonlocal executed
        executed = True

    with pytest.raises(SafeMCPToolError) as exc_info:
        intercept_mcp_tool_call(object(), _UndeclaredTestTool(), {}, execute)

    assert exc_info.value.code is MCPErrorCode.PROTECTION_UNAVAILABLE
    assert exc_info.value.retryable is False
    assert executed is False


def test_contract_inventory_rejects_an_undeclared_tool():
    class UndeclaredMCPTool(MCPTool):
        type = "undeclared_test_tool"

        def _sync_call(self, endpoint, args):
            return {}

    with pytest.raises(ImproperlyConfigured, match="undeclared_test_tool"):
        validate_mcp_tool_protection_contracts([UndeclaredMCPTool()])


def test_contract_inventory_rejects_a_tool_that_bypasses_the_base_call():
    class BypassingMCPTool(MCPTool):
        type = "list_databases"

        async def call(self, endpoint, call_arguments):
            return []

    with pytest.raises(ImproperlyConfigured, match="list_databases"):
        validate_mcp_tool_protection_contracts([BypassingMCPTool()])


class _DeclaredTestTool(MCPTool):
    type = "list_table_rows"

    def _sync_call(self, endpoint, args):
        return {}


class _UndeclaredTestTool(MCPTool):
    type = "undeclared_runtime_test_tool"

    def _sync_call(self, endpoint, args):
        return {}
