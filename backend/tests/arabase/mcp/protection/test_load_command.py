"""Characterization of the ``mcp_protection_load`` worker helpers.

The real-Redis canary is release-blocking but opt-in.  These tests run its
issue and redeem workers against an in-memory Redis shared through one
``fakeredis.FakeServer``, so every worker connection sees the same data, just
as the forked workers share one real Redis server.
"""

import fakeredis
import pytest

from arabase.management.commands import mcp_protection_load


@pytest.fixture
def shared_fake_redis(monkeypatch):
    server = fakeredis.FakeServer()
    monkeypatch.setattr(
        "arabase.management.commands.mcp_protection_load._connect",
        lambda url: fakeredis.FakeRedis(server=server, decode_responses=True),
    )
    return server


def test_issue_batch_issues_every_token_and_the_sample_redeems(shared_fake_redis):
    result = mcp_protection_load._issue_batch(("redis://unused", 7, 0, 3))

    assert result["ok"] is True
    assert result["issued"] == 3
    assert set(result) == {"ok", "issued", "duration_ms", "sample"}
    assert set(result["sample"]) == {"raw_handle", "binding", "value"}
    assert result["sample"]["value"] == "load-test-value-0-0"
    assert result["sample"]["binding"]["endpoint_id"] == 7
    assert result["sample"]["binding"]["row_id"] == 1

    assert mcp_protection_load._redeem_sample(("redis://unused", result["sample"]))
