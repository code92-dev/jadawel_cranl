import base64
import json
from contextlib import nullcontext

from django.db import transaction
from django.test import override_settings

import fakeredis
import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectionMutationAudit,
    MCPProtectionPolicy,
)
from arabase.mcp.protection.policy_state import safe_field_type_name
from arabase.mcp.protection.vault import (
    MASK_TOKEN_REDIS_PREFIX,
    MaskTokenVaultUnavailable,
    RedisMaskTokenVault,
)
from jadawel.contrib.database.fields.dependencies.models import FieldDependency
from jadawel.core.mcp import JadawelMCPServer, current_key
from jadawel.core.mcp.errors import SafeMCPToolError

FINGERPRINT_KEY = base64.b64encode(b"f" * 32).decode()


def _is_mask_token(value):
    return set(value) == {"$jadawelProtected"} and value["$jadawelProtected"]["v"] == 1


def _token_record_count(redis):
    return sum(
        len(key) == len(MASK_TOKEN_REDIS_PREFIX) + 64
        for key in redis.scan_iter(match=f"{MASK_TOKEN_REDIS_PREFIX}*")
    )


def _patch_vault(monkeypatch, vault, *, interceptor=False):
    """Serve ``vault`` from the egress seam, and the interceptor seam if asked."""

    monkeypatch.setattr(
        "arabase.mcp.protection.egress.get_mask_token_vault", lambda: vault
    )
    if interceptor:
        monkeypatch.setattr(
            "arabase.mcp.protection.interceptor.get_mask_token_vault", lambda: vault
        )


def _in_session(endpoint, script, *, atomic):
    """Run ``await script(client)`` in one MCP client session as ``endpoint``.

    ``atomic`` wraps the whole session in ``transaction.atomic()``.
    """

    mcp = JadawelMCPServer()
    key_token = current_key.set(endpoint.key)
    try:

        async def inner():
            async with client_session(mcp._mcp_server) as client:
                return await script(client)

        with transaction.atomic() if atomic else nullcontext():
            return async_to_sync(inner)()
    finally:
        current_key.reset(key_token)


def _call_tool(endpoint, tool_name, arguments, *, atomic):
    """Call one MCP tool as ``endpoint`` and return its result."""

    async def script(client):
        return await client.call_tool(tool_name, arguments)

    return _in_session(endpoint, script, atomic=atomic)


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_list_rows_masks_direct_values_but_preserves_true_empty_values(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    amount = data_fixture.create_number_field(name="Amount", table=table)
    approved = data_fixture.create_boolean_field(name="Approved", table=table)
    empty = data_fixture.create_text_field(name="Empty", table=table)
    for field in (secret, amount, approved, empty):
        MCPProtectedField.objects.create(
            policy=endpoint.arabase_protection_policy,
            field=field,
        )
    model = table.get_model(attribute_names=True)
    model.objects.create(
        secret="never leave Jadawel", amount=0, approved=False, empty=""
    )

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=True
    )

    assert result.isError is False
    serialized = result.content[0].text
    assert "never leave Jadawel" not in serialized
    row = json.loads(serialized)["results"][0]
    assert _is_mask_token(row["Secret"])
    assert _is_mask_token(row["Amount"])
    assert _is_mask_token(row["Approved"])
    assert row["Empty"] == ""
    assert _token_record_count(redis) == 3


@pytest.mark.django_db
def test_vault_configuration_failure_returns_only_safe_error_and_never_plaintext(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    model = table.get_model(attribute_names=True)
    model.objects.create(secret="vault outage canary")

    def unavailable_vault():
        raise MaskTokenVaultUnavailable

    monkeypatch.setattr(
        "arabase.mcp.protection.egress.get_mask_token_vault", unavailable_vault
    )
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=True
    )

    assert result.isError is True
    assert "vault outage canary" not in result.content[0].text
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_policy_revision_change_before_release_discards_complete_response(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    model = table.get_model(attribute_names=True)
    model.objects.create(secret="revision race canary")
    redis = fakeredis.FakeRedis(decode_responses=True)

    class RacingVault(RedisMaskTokenVault):
        def issue_many(self, items):
            issued = super().issue_many(items)
            MCPProtectionPolicy.objects.filter(endpoint=endpoint).update(revision=2)
            return issued

    vault = RacingVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=True
    )

    assert result.isError is True
    assert "revision race canary" not in result.content[0].text
    assert redis.dbsize() == 0


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_create_and_update_rows_mask_every_direct_protected_value(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)

    async def script(client):
        created = await client.call_tool(
            "create_rows",
            {"table_id": table.id, "rows": [{"Secret": "created canary"}]},
        )
        created_row = json.loads(created.content[0].text)[0]
        assert created.isError is False
        assert "created canary" not in created.content[0].text
        assert _is_mask_token(created_row["Secret"])

        updated = await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [{"id": created_row["id"], "Secret": "updated canary"}],
            },
        )
        updated_row = json.loads(updated.content[0].text)[0]
        assert updated.isError is False
        assert "updated canary" not in updated.content[0].text
        assert _is_mask_token(updated_row["Secret"])

    _in_session(endpoint, script, atomic=True)

    assert _token_record_count(redis) == 2


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_redis_interruption_rolls_back_a_protected_create_batch(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    redis = fakeredis.FakeRedis(decode_responses=True)

    class InterruptedVault(RedisMaskTokenVault):
        def issue_many(self, items):
            raise MaskTokenVaultUnavailable

    vault = InterruptedVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint,
        "create_rows",
        {
            "table_id": table.id,
            "rows": [
                {"Secret": "first interruption canary"},
                {"Secret": "second interruption canary"},
            ],
        },
        atomic=False,
    )

    assert result.isError is True
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )
    assert table.get_model(attribute_names=True).objects.count() == 0
    assert _token_record_count(redis) == 0


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_redis_interruption_rolls_back_a_two_hundred_row_update(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    model = table.get_model(attribute_names=True)
    rows = model.objects.bulk_create(
        [model(secret=f"before interruption {index}") for index in range(200)]
    )
    redis = fakeredis.FakeRedis(decode_responses=True)

    class InterruptedVault(RedisMaskTokenVault):
        def issue_many(self, items):
            raise MaskTokenVaultUnavailable

    vault = InterruptedVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint,
        "update_rows",
        {
            "table_id": table.id,
            "rows": [
                {"id": row.id, "Secret": f"after interruption {index}"}
                for index, row in enumerate(rows)
            ],
        },
        atomic=False,
    )

    assert result.isError is True
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )
    persisted = list(model.objects.order_by("id").values_list("secret", flat=True))
    assert persisted == [f"before interruption {index}" for index in range(200)]
    assert _token_record_count(redis) == 0
    assert (
        MCPProtectionMutationAudit.objects.filter(tool_type="update_rows").count() == 0
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_update_accepts_only_a_same_cell_preservation_token(data_fixture, monkeypatch):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    async def script(client):
        created = await client.call_tool(
            "create_rows", {"table_id": table.id, "rows": [{"Secret": "keep"}]}
        )
        created_row = json.loads(created.content[0].text)[0]
        preserved = await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [{"id": created_row["id"], "Secret": created_row["Secret"]}],
            },
        )
        return created_row, preserved

    created_row, preserved = _in_session(endpoint, script, atomic=True)

    assert preserved.isError is False
    assert json.loads(preserved.content[0].text)[0]["Secret"] != "keep"
    raw = table.get_model(attribute_names=True).objects.get(id=created_row["id"])
    assert raw.secret == "keep"


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_same_cell_preservation_uses_write_value_for_single_select(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_single_select_field(
        name="Status", table=table, primary=True
    )
    option = data_fixture.create_select_option(field=field, value="Keep", color="blue")
    model = table.get_model()
    row = model.objects.create()
    setattr(row, f"field_{field.id}_id", option.id)
    row.save()
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy,
        field=field,
    )

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    async def script(client):
        listed = await client.call_tool(
            "list_table_rows", {"table_id": table.id, "size": 1}
        )
        listed_row = json.loads(listed.content[0].text)["results"][0]
        preserved = await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [{"id": listed_row["id"], "Status": listed_row["Status"]}],
            },
        )
        return listed_row, preserved

    listed_row, preserved = _in_session(endpoint, script, atomic=False)

    assert preserved.isError is False
    preserved_row = json.loads(preserved.content[0].text)[0]
    assert _is_mask_token(preserved_row["Status"])
    assert preserved_row["Status"] != listed_row["Status"]
    assert getattr(model.objects.get(id=row.id), f"field_{field.id}_id") == option.id


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_update_omission_and_empty_values_follow_field_semantics(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    model = table.get_model(attribute_names=True)
    row = model.objects.create(secret="preserve me")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)
    captured_updates = []
    from jadawel.contrib.database.mcp import services as mcp_services

    original_update_rows = mcp_services.update_rows

    def capture_update_rows(*args, **kwargs):
        captured_updates.append(args[3])
        return original_update_rows(*args, **kwargs)

    monkeypatch.setattr(mcp_services, "update_rows", capture_update_rows)

    omitted = _call_tool(
        endpoint,
        "update_rows",
        {"table_id": table.id, "rows": [{"id": row.id}]},
        atomic=False,
    )
    omitted_value = model.objects.get(id=row.id).secret
    cleared = _call_tool(
        endpoint,
        "update_rows",
        {"table_id": table.id, "rows": [{"id": row.id, "Secret": ""}]},
        atomic=False,
    )

    assert omitted.isError is False
    omitted_row = json.loads(omitted.content[0].text)[0]
    assert _is_mask_token(omitted_row["Secret"])
    assert captured_updates[0][0]["Secret"] == "preserve me"
    assert omitted_value == "preserve me"

    assert cleared.isError is False
    assert json.loads(cleared.content[0].text)[0]["Secret"] == ""
    assert model.objects.get(id=row.id).secret == ""


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_copied_token_rejects_the_entire_update_batch(data_fixture, monkeypatch):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    model = table.get_model(attribute_names=True)
    first, second = model.objects.bulk_create(
        [model(secret="first"), model(secret="second")]
    )

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    async def script(client):
        listed = await client.call_tool(
            "list_table_rows", {"table_id": table.id, "size": 2}
        )
        rows = json.loads(listed.content[0].text)["results"]
        source = next(item for item in rows if item["id"] == first.id)
        return await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [
                    {"id": second.id, "Secret": source["Secret"]},
                ],
            },
        )

    copied = _in_session(endpoint, script, atomic=False)

    assert copied.isError is True
    assert json.loads(copied.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )
    assert model.objects.get(id=first.id).secret == "first"
    assert model.objects.get(id=second.id).secret == "second"
    assert (
        MCPProtectionMutationAudit.objects.filter(tool_type="update_rows").count() == 0
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_tokens_reject_cross_endpoint_cross_field_and_malformed_reuse(
    data_fixture, monkeypatch
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    secret = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    other = data_fixture.create_text_field(name="Other", table=table)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    foreign_endpoint = data_fixture.create_mcp_endpoint(
        user=user, workspace=workspace, name="Foreign endpoint"
    )
    for target in (endpoint, foreign_endpoint):
        MCPProtectedField.objects.bulk_create(
            [
                MCPProtectedField(
                    policy=target.arabase_protection_policy,
                    field=secret,
                ),
                MCPProtectedField(
                    policy=target.arabase_protection_policy,
                    field=other,
                ),
            ]
        )
    model = table.get_model(attribute_names=True)
    row = model.objects.create(secret="secret", other="other")
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    listed = _call_tool(
        endpoint,
        "list_table_rows",
        {"table_id": table.id, "size": 1},
        atomic=False,
    )
    listed_row = json.loads(listed.content[0].text)["results"][0]
    source_token = listed_row["Secret"]

    foreign = _call_tool(
        foreign_endpoint,
        "update_rows",
        {"table_id": table.id, "rows": [{"id": row.id, "Secret": source_token}]},
        atomic=False,
    )
    copied_to_other_field = _call_tool(
        endpoint,
        "update_rows",
        {"table_id": table.id, "rows": [{"id": row.id, "Other": source_token}]},
        atomic=False,
    )
    malformed_create = _call_tool(
        endpoint,
        "create_rows",
        {
            "table_id": table.id,
            "rows": [{"Secret": {"$jadawelProtected": {"v": 1, "token": "malformed"}}}],
        },
        atomic=False,
    )

    for result in (foreign, copied_to_other_field, malformed_create):
        assert result.isError is True
        assert json.loads(result.content[0].text)["error"]["code"] == (
            "PROTECTION_UNAVAILABLE"
        )
    row.refresh_from_db()
    assert row.secret == "secret"
    assert row.other == "other"
    assert model.objects.count() == 1


@pytest.mark.django_db
def test_protected_search_is_rejected_before_row_query(data_fixture, monkeypatch):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )

    def query_must_not_run(*args, **kwargs):
        raise AssertionError("protected searches must be rejected before querying")

    monkeypatch.setattr(
        "jadawel.contrib.database.mcp.services.list_rows", query_must_not_run
    )
    result = _call_tool(
        endpoint,
        "list_table_rows",
        {"table_id": table.id, "search": "sensitive"},
        atomic=False,
    )

    assert result.isError is True
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )


@pytest.mark.django_db
def test_protection_on_another_table_leaves_unprotected_search_unchanged(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    protected_table = data_fixture.create_database_table(database=database)
    protected_field = data_fixture.create_text_field(
        name="Secret", table=protected_table, primary=True
    )
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected_field
    )
    public_table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(name="Name", table=public_table, primary=True)
    public_table.get_model(attribute_names=True).objects.create(name="search canary")

    def vault_must_not_be_used():
        raise AssertionError("unprotected tables do not need the token vault")

    monkeypatch.setattr(
        "arabase.mcp.protection.egress.get_mask_token_vault", vault_must_not_be_used
    )
    result = _call_tool(
        endpoint,
        "list_table_rows",
        {"table_id": public_table.id, "search": "search canary"},
        atomic=True,
    )

    assert result.isError is False
    assert json.loads(result.content[0].text)["results"][0]["Name"] == "search canary"


@pytest.mark.django_db
def test_token_envelopes_are_rejected_on_unprotected_table_mutations(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    protected_table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(
        name="Secret", table=protected_table, primary=True
    )
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )
    public_table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(name="Payload", table=public_table, primary=True)
    envelope = {"$jadawelProtected": {"v": 1, "token": "not-a-valid-handle"}}

    async def script(client):
        created = await client.call_tool(
            "create_rows",
            {"table_id": public_table.id, "rows": [{"Payload": envelope}]},
        )
        ordinary = await client.call_tool(
            "create_rows",
            {"table_id": public_table.id, "rows": [{"Payload": "plain"}]},
        )
        ordinary_row = json.loads(ordinary.content[0].text)[0]
        updated = await client.call_tool(
            "update_rows",
            {
                "table_id": public_table.id,
                "rows": [{"id": ordinary_row["id"], "Payload": envelope}],
            },
        )
        return created, updated

    created, updated = _in_session(endpoint, script, atomic=False)

    for result in (created, updated):
        assert result.isError is True
        assert json.loads(result.content[0].text)["error"]["code"] == (
            "PROTECTION_UNAVAILABLE"
        )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_unrelated_broken_dependency_does_not_block_protected_rows(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )

    unrelated_table = data_fixture.create_database_table(database=database)
    unrelated = data_fixture.create_text_field(name="Broken", table=unrelated_table)
    FieldDependency.objects.create(
        dependant=unrelated,
        dependency=None,
        broken_reference_field_name="Missing field",
    )
    table.get_model(attribute_names=True).objects.create(secret="protected canary")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=True
    )

    assert result.isError is False
    serialized = result.content[0].text
    assert "protected canary" not in serialized
    assert _is_mask_token(json.loads(serialized)["results"][0]["Secret"])


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_cross_table_dependant_is_not_added_to_target_row_output(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )
    other_table = data_fixture.create_database_table(database=database)
    dependant = data_fixture.create_text_field(name="Derived", table=other_table)
    FieldDependency.objects.create(dependant=dependant, dependency=protected)
    table.get_model(attribute_names=True).objects.create(secret="protected canary")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=False
    )

    assert result.isError is False
    row = json.loads(result.content[0].text)["results"][0]
    assert _is_mask_token(row["Secret"])
    assert "Derived" not in row


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_broken_dependency_on_a_protected_field_still_fails_closed(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )
    FieldDependency.objects.create(
        dependant=protected,
        dependency=None,
        broken_reference_field_name="Missing field",
    )
    table.get_model(attribute_names=True).objects.create(secret="protected canary")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=True
    )

    assert result.isError is True
    assert "protected canary" not in result.content[0].text
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_derived_protected_leaf_is_masked_and_display_token_cannot_mutate(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    derived = data_fixture.create_text_field(name="Derived label", table=table)
    FieldDependency.objects.create(dependant=derived, dependency=protected)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy,
        field=protected,
    )
    model = table.get_model(attribute_names=True)
    model.objects.create(secret="derived source canary", derived_label="derived canary")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    async def script(client):
        listed = await client.call_tool(
            "list_table_rows", {"table_id": table.id, "size": 1}
        )
        row = json.loads(listed.content[0].text)["results"][0]
        rejected = await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [{"id": row["id"], "Derived label": row["Derived label"]}],
            },
        )
        return listed, row, rejected

    listed, row, rejected = _in_session(endpoint, script, atomic=False)

    assert listed.isError is False
    serialized = listed.content[0].text
    assert "derived source canary" not in serialized
    assert "derived canary" not in serialized
    assert _is_mask_token(row["Secret"])
    assert _is_mask_token(row["Derived label"])
    assert rejected.isError is True
    assert json.loads(rejected.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )


@pytest.mark.django_db
def test_cycle_in_protected_provenance_fails_closed(data_fixture, monkeypatch):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    derived = data_fixture.create_text_field(name="Derived", table=table)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )
    FieldDependency.objects.create(dependant=derived, dependency=protected)
    FieldDependency.objects.create(dependant=protected, dependency=derived)
    table.get_model(attribute_names=True).objects.create(secret="cycle canary")

    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault)
    result = _call_tool(
        endpoint, "list_table_rows", {"table_id": table.id}, atomic=False
    )

    assert result.isError is True
    assert "cycle canary" not in result.content[0].text
    assert json.loads(result.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )


@pytest.mark.django_db
def test_unknown_protected_field_adapter_fails_closed_with_safe_error(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    protected = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=protected
    )

    def broken_adapter(_field):
        raise RuntimeError("adapter details must not cross the MCP boundary")

    monkeypatch.setattr(type(protected), "get_type", broken_adapter)

    with pytest.raises(SafeMCPToolError) as exc_info:
        safe_field_type_name(protected)

    assert exc_info.value.code.name == "PROTECTION_UNAVAILABLE"
    assert exc_info.value.retryable is False


@pytest.mark.django_db
@override_settings(
    MCP_PROTECTION_FINGERPRINT_KEYS={"current": FINGERPRINT_KEY},
    MCP_PROTECTION_ACTIVE_KEY_ID="current",
)
def test_two_hundred_row_update_is_all_or_nothing_on_invalid_token(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(name="Secret", table=table, primary=True)
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy, field=field
    )
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    _patch_vault(monkeypatch, vault, interceptor=True)

    async def script(client):
        created = await client.call_tool(
            "create_rows",
            {
                "table_id": table.id,
                "rows": [{"Secret": f"batch-{index}"} for index in range(200)],
            },
        )
        assert created.isError is False
        created_rows = json.loads(created.content[0].text)
        failed = await client.call_tool(
            "update_rows",
            {
                "table_id": table.id,
                "rows": [
                    {
                        "id": created_rows[0]["id"],
                        "Secret": created_rows[0]["Secret"],
                    },
                    {
                        "id": created_rows[1]["id"],
                        "Secret": {"$jadawelProtected": {"v": 1, "token": "invalid"}},
                    },
                ],
            },
        )
        return created_rows, failed

    created_rows, failed = _in_session(endpoint, script, atomic=True)

    assert failed.isError is True
    assert json.loads(failed.content[0].text)["error"]["code"] == (
        "PROTECTION_UNAVAILABLE"
    )
    model = table.get_model(attribute_names=True)
    assert model.objects.get(id=created_rows[0]["id"]).secret == "batch-0"
    assert model.objects.get(id=created_rows[1]["id"]).secret == "batch-1"
    assert (
        MCPProtectionMutationAudit.objects.filter(tool_type="update_rows").count() == 0
    )
