import base64
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from django.db import connection, connections, transaction
from django.test import override_settings

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

import arabase.mcp.protection.vault as vault_module
from arabase.mcp.protection.models import MCPMaskTokenRecord, MCPProtectedField
from arabase.mcp.protection.readiness import check_mask_token_vault_readiness
from arabase.mcp.protection.tokens import extract_mask_token_handle
from arabase.mcp.protection.vault import (
    DERIVED_FINGERPRINT_KEY_ID,
    DatabaseMaskTokenVault,
    MaskTokenBinding,
    MaskTokenVaultUnavailable,
    RedisMaskTokenVault,
    get_mask_token_vault,
    purge_expired_mask_tokens,
)
from jadawel.core.mcp import JadawelMCPServer, current_key

EXPLICIT_KEY = base64.b64encode(b"e" * 32).decode()


def _binding(endpoint, **overrides):
    values = {
        "endpoint_id": endpoint.id,
        "workspace_id": endpoint.workspace_id,
        "table_id": 11,
        "row_id": 7,
        "field_id": 13,
        "policy_revision": 2,
        "access_generation": 2,
        "operation_class": "preserve_cell",
        "observed_row_state": "2026-09-23T10:00:00+00:00",
        "field_type": "text",
    }
    values.update(overrides)
    return MaskTokenBinding(**values)


@override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
)
def test_auto_backend_keeps_tokens_in_the_database_without_redis():
    assert isinstance(get_mask_token_vault(), DatabaseMaskTokenVault)


@override_settings(MCP_PROTECTION_VAULT="auto", MCP_PROTECTION_REDIS_URL="redis://x")
def test_auto_backend_prefers_a_configured_dedicated_redis():
    assert isinstance(get_mask_token_vault(), RedisMaskTokenVault)


@override_settings(MCP_PROTECTION_VAULT="memcached")
def test_unknown_backend_fails_closed():
    with pytest.raises(MaskTokenVaultUnavailable):
        get_mask_token_vault()


@pytest.mark.django_db
@override_settings(MCP_PROTECTION_FINGERPRINT_KEYS={}, MCP_PROTECTION_ACTIVE_KEY_ID="")
def test_database_vault_stores_only_digests_and_redeems_only_the_same_cell(
    data_fixture,
):
    endpoint = data_fixture.create_mcp_endpoint()
    vault = DatabaseMaskTokenVault()
    binding = _binding(endpoint)

    issued = vault.issue(binding, "national id canary")

    record = MCPMaskTokenRecord.objects.get()
    stored = json.dumps(record.record)
    assert record.digest == issued.digest
    assert issued.raw_handle not in stored
    assert "national id canary" not in stored
    assert record.record["fingerprint_key_id"] == DERIVED_FINGERPRINT_KEY_ID
    handle = extract_mask_token_handle(issued.envelope)
    assert vault.redeem(handle, binding, "national id canary") is True
    # Non-consuming: the same token can be redeemed again.
    assert vault.redeem(handle, binding, "national id canary") is True
    assert vault.redeem(handle, binding, "a changed value") is False
    assert (
        vault.redeem(handle, replace(binding, row_id=8), "national id canary") is False
    )
    assert (
        vault.redeem(
            handle,
            replace(binding, operation_class="display_only"),
            "national id canary",
        )
        is False
    )


@pytest.mark.django_db
def test_database_vault_ignores_and_purges_expired_tokens(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    vault = DatabaseMaskTokenVault()
    binding = _binding(endpoint)
    issued = vault.issue(binding, "value")
    MCPMaskTokenRecord.objects.update(
        expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )

    handle = extract_mask_token_handle(issued.envelope)
    assert vault.redeem(handle, binding, "value") is False
    assert purge_expired_mask_tokens() == 1
    assert MCPMaskTokenRecord.objects.count() == 0


@pytest.mark.django_db
def test_database_vault_rejects_an_over_capacity_batch_without_partial_records(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    vault = DatabaseMaskTokenVault()
    monkeypatch.setattr(vault_module, "MAX_ENDPOINT_TOKENS", 2)
    vault.issue(_binding(endpoint), "first")

    with pytest.raises(MaskTokenVaultUnavailable):
        vault.issue_many(
            [
                (_binding(endpoint, row_id=8), "second"),
                (_binding(endpoint, row_id=9), "third"),
            ]
        )

    assert MCPMaskTokenRecord.objects.count() == 1


@pytest.mark.django_db
def test_configuring_an_explicit_keyring_revokes_derived_tokens(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    vault = DatabaseMaskTokenVault()
    binding = _binding(endpoint)
    with override_settings(
        MCP_PROTECTION_FINGERPRINT_KEYS={}, MCP_PROTECTION_ACTIVE_KEY_ID=""
    ):
        issued = vault.issue(binding, "value")
    handle = extract_mask_token_handle(issued.envelope)

    with override_settings(
        MCP_PROTECTION_FINGERPRINT_KEYS={"current": EXPLICIT_KEY},
        MCP_PROTECTION_ACTIVE_KEY_ID="current",
    ):
        assert vault.redeem(handle, binding, "value") is False
        explicit = vault.issue(replace(binding, row_id=8), "value")
        assert (
            vault.redeem(
                extract_mask_token_handle(explicit.envelope),
                replace(binding, row_id=8),
                "value",
            )
            is True
        )


@override_settings(SECRET_KEY="first-secret")
def test_derived_key_changes_with_secret_key():
    first = vault_module._derived_fingerprint_key()
    with override_settings(SECRET_KEY="second-secret"):
        second = vault_module._derived_fingerprint_key()

    assert len(first) == 32
    assert first != second


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_VAULT="database",
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="",
)
def test_database_vault_is_ready_with_no_configuration():
    assert check_mask_token_vault_readiness().ready is True


@pytest.mark.django_db(transaction=True)
def test_database_issuer_admission_fails_closed_while_the_endpoint_is_saturated(
    data_fixture, monkeypatch
):
    from arabase.mcp.protection import capacity

    monkeypatch.setattr(capacity, "ISSUER_WAIT_SECONDS", 0.05)
    endpoint = data_fixture.create_mcp_endpoint()
    vault = DatabaseMaskTokenVault()
    other = connections.create_connection("default")
    try:
        other.set_autocommit(False)
        with other.cursor() as cursor:
            for slot in range(capacity.MAX_ACTIVE_ISSUERS_PER_ENDPOINT):
                cursor.execute(
                    "SELECT pg_try_advisory_xact_lock(%s)",
                    [vault_module._ISSUER_ENDPOINT_LOCK_BASE + endpoint.id * 4 + slot],
                )
                assert cursor.fetchone()[0] is True

        with pytest.raises(MaskTokenVaultUnavailable):
            with vault.issuance_lease(endpoint.id):
                pass

        # Another endpoint is unaffected.
        with vault.issuance_lease(endpoint.id + 1):
            pass

        # The locks are transaction-scoped: ending the holder's transaction,
        # as a crashed worker's connection would, frees the slots.
        other.rollback()
        with vault.issuance_lease(endpoint.id):
            pass
    finally:
        other.close()
    assert connection.in_atomic_block is False


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="",
)
def test_list_rows_masks_protected_values_with_no_vault_configuration(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    public = data_fixture.create_text_field(name="Public", table=table)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=secret
    )
    model = table.get_model(attribute_names=True)
    model.objects.create(secret="never leave Jadawel", public="shown")
    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)

    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                return await client.call_tool("list_table_rows", {"table_id": table.id})

        with transaction.atomic():
            result = async_to_sync(inner)()
    finally:
        current_key.reset(key_token)

    assert result.isError is False
    assert "never leave Jadawel" not in result.content[0].text
    row = json.loads(result.content[0].text)["results"][0]
    assert set(row["Secret"]) == {"$jadawelProtected"}
    assert row["Public"] == "shown"
    assert MCPMaskTokenRecord.objects.filter(endpoint=endpoint).count() == 1
