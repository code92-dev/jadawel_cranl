from django.conf import settings

from rest_framework.exceptions import ValidationError

from arabase.mcp.protection.readiness import check_mask_token_vault_readiness

MCP_PROTECTION_STAFF_FLAG = "mcp-protected-fields-staff"
MCP_PROTECTION_FLAG = "mcp-protected-fields"


def ensure_policy_admission_allowed(user) -> None:
    """Gate policy admission without ever weakening enforcement.

    Every owner may protect fields: the vault needs no setup and
    ``ensure_protection_vault_ready`` refuses admission when it is not ready.
    ``mcp-protected-fields-staff`` alone restricts admission to staff for a
    staged rollout; ``mcp-protected-fields`` (or ``*``) lifts that restriction
    and is otherwise no longer needed.
    """

    configured_flags = settings.FEATURE_FLAGS
    if isinstance(configured_flags, str):
        configured_flags = (configured_flags,)
    flags = {str(flag).strip().lower() for flag in configured_flags}
    if "*" in flags or MCP_PROTECTION_FLAG in flags:
        return
    if MCP_PROTECTION_STAFF_FLAG not in flags or user.is_staff:
        return
    raise ValidationError(
        {
            "protected_field_ids": (
                "MCP protected-field policies are not enabled for this account."
            )
        }
    )


class MCPProtectionVaultNotReady(Exception):
    """Protecting a field now would leave every read of its table blocked."""

    def __init__(self, safe_reason_code: str):
        super().__init__(safe_reason_code)
        self.safe_reason_code = safe_reason_code


def ensure_protection_vault_ready() -> None:
    """Refuse to protect a new field while protected reads would fail closed.

    Enforcement never depends on this check: a policy saved before an outage
    still blocks reads. It only stops an owner from creating an endpoint whose
    protected tables are unreadable from the start. Removing protection is never
    gated, so an owner can always recover during an outage.
    """

    readiness = check_mask_token_vault_readiness()
    if not readiness.ready:
        raise MCPProtectionVaultNotReady(readiness.safe_reason_code)
