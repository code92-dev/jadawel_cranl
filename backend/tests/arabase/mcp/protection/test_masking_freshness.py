"""Masking freshness: the time-of-check/time-of-use guard.

A derived field can start depending on a protected field between the moment a
policy snapshot is taken and the moment the row payload is read.  Masking must
recompute the protected-output graph after the read, never from a snapshot taken
before it, so the new derived field is masked.  These tests pin that at the
egress seam, at the interceptor and in the ``get_page_view`` sample.
"""

from django.test import override_settings

import pytest

from arabase.mcp.page import services as page_services
from arabase.mcp.protection import egress, interceptor
from arabase.mcp.protection.models import MCPProtectedField
from arabase.mcp.protection.policy_state import get_mcp_protection_policy_state
from arabase.views.view_types import HtmlPageViewType
from jadawel.contrib.database.fields.handler import FieldHandler
from jadawel.contrib.database.mcp import services as row_services
from jadawel.contrib.database.views.handler import ViewHandler
from jadawel.core.mcp.registries import mcp_tool_registry

PAGE_V1 = "<!doctype html><body><h1>v1</h1></body>"
DERIVED_NAME = "Derived"

# The database vault keeps mask tokens in PostgreSQL, so no Redis is needed.
database_vault = override_settings(
    MCP_PROTECTION_VAULT="auto",
    MCP_PROTECTION_REDIS_URL="",
    MCP_PROTECTION_ALLOW_SHARED_REDIS=False,
    MCP_PROTECTION_FINGERPRINT_KEYS={},
    MCP_PROTECTION_ACTIVE_KEY_ID="",
)


class Protected:
    """Endpoint E protects Secret on table T, which has two rows."""

    def __init__(self, data_fixture):
        self.user = data_fixture.create_user()
        self.workspace = data_fixture.create_workspace(user=self.user)
        database = data_fixture.create_database_application(workspace=self.workspace)
        self.table = data_fixture.create_database_table(database=database)
        self.secret = data_fixture.create_text_field(
            table=self.table, name="Secret", primary=True
        )
        self.visible = data_fixture.create_text_field(table=self.table, name="Visible")
        self.endpoint = data_fixture.create_mcp_endpoint(
            user=self.user, workspace=self.workspace
        )
        MCPProtectedField.objects.create(
            policy=self.endpoint.arabase_protection_policy, field=self.secret
        )
        model = self.table.get_model()
        for index in range(2):
            model.objects.create(
                **{
                    f"field_{self.secret.id}": f"freshness canary {index}",
                    f"field_{self.visible.id}": f"shown {index}",
                }
            )

    def create_derived_field(self):
        return FieldHandler().create_field(
            self.user,
            self.table,
            "formula",
            name=DERIVED_NAME,
            formula="field('Secret')",
        )

    def list_rows(self):
        return row_services.list_rows(self.user, self.workspace, self.table.id)


@pytest.fixture
def protected(data_fixture):
    return Protected(data_fixture)


def _is_mask_envelope(value):
    return (
        isinstance(value, dict)
        and set(value) == {"$jadawelProtected"}
        and value["$jadawelProtected"]["v"] == 1
        and isinstance(value["$jadawelProtected"]["token"], str)
    )


def _assert_derived_cells_masked(rows):
    assert len(rows) == 2
    for row in rows:
        assert _is_mask_envelope(row[DERIVED_NAME])
        assert _is_mask_envelope(row["Secret"])
        assert row["Visible"].startswith("shown ")
    assert "freshness canary" not in str(rows)


@pytest.mark.django_db
@database_vault
def test_egress_masks_a_derived_field_created_after_the_policy_snapshot(protected):
    policy = get_mcp_protection_policy_state(protected.endpoint)
    protected.create_derived_field()
    result = protected.list_rows()
    # The unmasked read really carries the derived plaintext.
    assert result["results"][0][DERIVED_NAME].startswith("freshness canary")

    masked = egress.mask_table_rows(
        protected.endpoint,
        protected.table.id,
        result,
        policy,
    )

    _assert_derived_cells_masked(masked["results"])


@pytest.mark.django_db
@database_vault
def test_interceptor_masks_a_derived_field_created_during_execute(protected):
    tool = mcp_tool_registry.get("list_table_rows")
    args = tool.input_schema.model_validate({"table_id": protected.table.id})

    def execute():
        protected.create_derived_field()
        return protected.list_rows()

    # Observed: creating a derived field does not bump the policy revision, so
    # the call succeeds and the derived cells are masked (fail-closed).
    result = interceptor.intercept_mcp_tool_call(
        protected.endpoint, tool, args, execute
    )

    _assert_derived_cells_masked(result["results"])


@pytest.mark.django_db
@database_vault
def test_get_page_view_masks_a_derived_field_created_during_the_sample_read(
    protected, monkeypatch
):
    view = ViewHandler().create_view(
        protected.user,
        protected.table,
        HtmlPageViewType.type,
        name="Report",
        html=PAGE_V1,
    )
    real_serialize = page_services.serialize_rows_for_response
    calls = []

    def serialize_after_creating_the_derived_field(rows, model, **kwargs):
        calls.append(len(rows))
        protected.create_derived_field()
        fresh_model = protected.table.get_model()
        fresh_rows = list(
            fresh_model.objects.filter(id__in=[row.id for row in rows]).order_by(
                "order", "id"
            )
        )
        return real_serialize(fresh_rows, fresh_model, **kwargs)

    monkeypatch.setattr(
        page_services,
        "serialize_rows_for_response",
        serialize_after_creating_the_derived_field,
    )

    result = page_services.get_page_view(
        protected.user,
        protected.workspace,
        view.id,
        endpoint=protected.endpoint,
    )

    assert calls == [2]
    assert result["html"] is None
    assert result["row_count"] == 2
    _assert_derived_cells_masked(result["row_sample"])
