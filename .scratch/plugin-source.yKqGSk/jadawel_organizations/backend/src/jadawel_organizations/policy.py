"""Small policy hooks consumed by optional public-sharing integrations."""

from typing import Any

from .models import Organization, OrganizationWorkspace


def public_workspace_allowed(workspace: Any) -> bool:
    """Return whether public links may expose an organization workspace.

    An unmanaged workspace keeps Jadawel's existing behavior. Managed
    workspaces retain their share records while an organization is suspended
    or its billing entitlement is restricted; callers treat ``False`` as a
    not-found response so existing links stop serving data.
    """

    binding = (
        OrganizationWorkspace.objects.select_related("organization")
        .filter(workspace_id=workspace.pk)
        .first()
    )
    if binding is None:
        return True
    if binding.organization.status != Organization.Status.ACTIVE:
        return False
    from jadawel_billing.entitlements import get_effective_entitlements

    source = get_effective_entitlements(binding.organization.billing_account_id)[
        "source"
    ]
    return source not in {"restricted", "suspended"}
