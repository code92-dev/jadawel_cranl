import fakeredis
import pytest
from redis.exceptions import RedisError

import arabase.mcp.protection.readiness as readiness
from arabase.mcp.protection import limits
from arabase.mcp.protection.models import MCPProtectedField
from arabase.mcp.protection.vault import MaskTokenVaultUnavailable, RedisMaskTokenVault
from arabase.mcp.protection.vault.redis_backend import (
    ISSUER_ENDPOINT_INDEX_PREFIX,
    ISSUER_INDEX,
    issuance_lease,
)


def test_issuance_lease_enforces_endpoint_cap_and_releases(monkeypatch):
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    monkeypatch.setattr(limits, "ISSUER_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(limits, "MAX_ACTIVE_ISSUERS_PER_ENDPOINT", 1)

    first = issuance_lease(endpoint_id=7, vault=vault)
    first.__enter__()
    try:
        with pytest.raises(MaskTokenVaultUnavailable):
            with issuance_lease(endpoint_id=7, vault=vault):
                pass
    finally:
        first.__exit__(None, None, None)

    with issuance_lease(endpoint_id=7, vault=vault):
        assert redis.zcard(ISSUER_INDEX) == 1

    assert redis.zcard(ISSUER_INDEX) == 0


def test_issuance_lease_enforces_global_cap_and_reclaims_expired_workers(monkeypatch):
    redis = fakeredis.FakeRedis(decode_responses=True)
    vault = RedisMaskTokenVault(redis_client=redis)
    monkeypatch.setattr(limits, "ISSUER_WAIT_SECONDS", 0.03)
    monkeypatch.setattr(limits, "MAX_ACTIVE_ISSUERS_PER_ENDPOINT", 1)
    monkeypatch.setattr(limits, "MAX_ACTIVE_ISSUERS_GLOBAL", 2)

    first = issuance_lease(endpoint_id=7, vault=vault)
    first.__enter__()
    second = issuance_lease(endpoint_id=8, vault=vault)
    second.__enter__()
    try:
        with pytest.raises(MaskTokenVaultUnavailable):
            with issuance_lease(endpoint_id=9, vault=vault):
                pass

        # A worker that dies after admission leaves only its short lease. The
        # Lua admission step must remove that expired member before counting.
        members = redis.zrange(ISSUER_INDEX, 0, -1)
        assert len(members) == 2
        for member in members:
            redis.zadd(ISSUER_INDEX, {member: 0})
        for endpoint_id in (7, 8):
            endpoint_key = f"{ISSUER_ENDPOINT_INDEX_PREFIX}{endpoint_id}"
            for member in redis.zrange(endpoint_key, 0, -1):
                redis.zadd(endpoint_key, {member: 0})

        with issuance_lease(endpoint_id=9, vault=vault):
            assert redis.zcard(ISSUER_INDEX) == 1
    finally:
        second.__exit__(None, None, None)
        first.__exit__(None, None, None)


def _protect_one_field(data_fixture):
    """Create an endpoint whose policy protects one text field."""

    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table, name="Protected")
    MCPProtectedField.objects.create(
        policy=endpoint.arabase_protection_policy,
        field=field,
    )


@pytest.mark.django_db
def test_readiness_fails_closed_when_vault_is_unreachable(data_fixture, monkeypatch):
    _protect_one_field(data_fixture)

    redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis, "ping", lambda: (_ for _ in ()).throw(RedisError()))
    vault = RedisMaskTokenVault(redis_client=redis)
    monkeypatch.setattr(readiness, "get_mask_token_vault", lambda: vault)

    result = readiness.check_mcp_protection_policy_readiness()

    assert result.ready is False
    assert result.safe_reason_code == "PROTECTION_REDIS_UNAVAILABLE"


@pytest.mark.django_db
def test_readiness_alerts_and_rejects_at_memory_safety_floor(
    data_fixture, monkeypatch, caplog
):
    _protect_one_field(data_fixture)

    redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(
        redis,
        "config_get",
        lambda name: (
            {"maxmemory": "100"}
            if name == "maxmemory"
            else {"maxmemory-policy": "noeviction"}
        ),
    )
    monkeypatch.setattr(redis, "info", lambda section: {"used_memory": 70})
    vault = RedisMaskTokenVault(redis_client=redis)
    monkeypatch.setattr(readiness, "get_mask_token_vault", lambda: vault)

    with caplog.at_level("ERROR", logger="arabase.mcp.protection.readiness"):
        result = readiness.check_mcp_protection_policy_readiness()

    assert result.ready is False
    assert result.safe_reason_code == "PROTECTION_REDIS_UNAVAILABLE"
    assert "MCP protection Redis memory alert" in caplog.text
