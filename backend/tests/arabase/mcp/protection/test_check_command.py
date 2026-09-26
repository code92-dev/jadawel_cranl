from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

import pytest

from arabase.mcp.protection.models import MCPProtectedField, MCPProtectionPolicy


@pytest.mark.django_db
def test_protection_check_strict_passes_for_a_consistent_empty_policy(data_fixture):
    data_fixture.create_mcp_endpoint()
    output = StringIO()

    call_command("mcp_protection_check", "--strict", stdout=output)

    assert output.getvalue().strip() == "MCP protection check passed"


@pytest.mark.django_db
def test_protection_check_strict_reports_a_missing_policy_without_secrets(
    data_fixture,
):
    endpoint = data_fixture.create_mcp_endpoint()
    MCPProtectionPolicy.objects.filter(endpoint=endpoint).delete()
    output = StringIO()

    with pytest.raises(CommandError, match="POLICY_COUNT_MISMATCH") as exc_info:
        call_command("mcp_protection_check", "--strict", stdout=output)

    assert endpoint.key not in str(exc_info.value)
    assert "MCP protection check failed: POLICY_COUNT_MISMATCH" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Characterization: exact violation lists, duplicates included
# ---------------------------------------------------------------------------

# The database vault keeps mask tokens in PostgreSQL, so no Redis is needed.
database_vault = override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="",
)


def _protect_new_field(data_fixture, endpoint, workspace=None):
    database = data_fixture.create_database_application(
        workspace=workspace or endpoint.workspace
    )
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)
    return MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )


def _check_failure(*options) -> str:
    with pytest.raises(CommandError) as exc_info:
        call_command("mcp_protection_check", *options, stdout=StringIO())
    return str(exc_info.value)


@pytest.mark.django_db
@database_vault
def test_protection_check_reports_a_cross_workspace_relation_twice(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    _protect_new_field(
        data_fixture, endpoint, workspace=data_fixture.create_workspace()
    )

    assert _check_failure("--strict") == (
        "MCP protection check failed: POLICY_RELATION_INVALID, POLICY_RELATION_INVALID"
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
    MCP_PROTECTION_FINGERPRINT_KEYS={"k": "not-base64"},
    MCP_PROTECTION_ACTIVE_KEY_ID="k",
)
def test_protection_check_reports_an_invalid_fingerprint_key(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    _protect_new_field(data_fixture, endpoint)

    assert _check_failure("--strict") == (
        "MCP protection check failed: FINGERPRINT_KEY_INVALID, "
        "PROTECTION_KEY_UNAVAILABLE"
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_VAULT="redis",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="",
)
def test_protection_check_reports_a_redis_vault_without_a_url(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    _protect_new_field(data_fixture, endpoint)

    assert _check_failure("--strict") == (
        "MCP protection check failed: DEDICATED_REDIS_REQUIRED, "
        "PROTECTION_REDIS_UNAVAILABLE"
    )


@pytest.mark.django_db
@database_vault
def test_protection_check_reports_a_count_mismatch_twice_with_active_protection(
    data_fixture,
):
    endpoint = data_fixture.create_mcp_endpoint()
    _protect_new_field(data_fixture, endpoint)
    other = data_fixture.create_mcp_endpoint()
    MCPProtectionPolicy.objects.filter(endpoint=other).delete()

    assert _check_failure("--strict") == (
        "MCP protection check failed: POLICY_COUNT_MISMATCH, POLICY_COUNT_MISMATCH"
    )


@pytest.mark.django_db
@database_vault
def test_protection_check_without_strict_only_warns(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    _protect_new_field(
        data_fixture, endpoint, workspace=data_fixture.create_workspace()
    )
    output = StringIO()

    call_command("mcp_protection_check", stdout=output)

    assert output.getvalue().strip() == "MCP protection warnings present"
