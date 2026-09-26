from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

from arabase.mcp.protection.models import MCPProtectionMutationAudit

_active_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "mcp_protection_audit_context", default=None
)


def is_content_blind_mcp_mutation() -> bool:
    return _active_context.get() is not None


@contextmanager
def content_blind_mcp_mutation(
    *,
    endpoint,
    tool_type: str,
    table_id: int,
    row_count: int,
    policy_revision: int,
    access_generation: int,
    protected_field_ids: tuple[int, ...],
) -> Iterator[None]:
    audit = {
        "endpoint_id": endpoint.id,
        "actor_id": endpoint.user_id,
        "tool_type": tool_type,
        "table_id": table_id,
        "row_count": row_count,
        "policy_revision": policy_revision,
        "access_generation": access_generation,
        "protected_field_ids": list(protected_field_ids),
    }
    token = _active_context.set(audit)
    try:
        yield
        MCPProtectionMutationAudit.objects.create(**audit, outcome="success")
    finally:
        _active_context.reset(token)
