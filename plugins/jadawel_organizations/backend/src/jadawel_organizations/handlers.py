"""Public entry point for organization handlers.

The handlers live in modules split by concern, each importing only from the
layers below it:

- access.py: actor checks, audit logging and invitation helpers.
- workspace_access.py: workspace binding and managed workspace access.
- provisioning.py: organization creation, Team provisioning and owner setup.
- members.py: invitations and membership changes.
- lifecycle.py: organization settings, snapshots and status transitions.

This module re-exports every handler, so existing
``jadawel_organizations.handlers`` imports keep resolving to the same objects.
"""

from .access import (
    User,
    _can_manage,
    _invitation_expires_at,
    _membership,
    _pending_owner_invitations,
    _require_actor,
    _require_workspace_admin,
    audit,
    reject_legacy_workspace_membership_mutation,
)
from .lifecycle import (
    change_organization_lifecycle,
    organization_snapshot,
    transition_to_personal,
    update_organization,
)
from .members import (
    accept_invitation,
    add_member,
    invite_member,
    remove_member,
    revoke_invitation,
    update_member,
)
from .provisioning import (
    _issue_owner_setup_invitation,
    create_organization,
    create_pending_team,
    provision_paid_team,
    reassign_owner_setup,
    resend_owner_setup,
    team_occupied_seats,
)
from .workspace_access import (
    _disconnect_user_after_commit,
    _grant_owner_workspace_admin,
    _remove_workspace_user,
    _sync_member,
    _sync_workspace_user,
    assign_workspace_member,
    bind_workspace,
    unassign_workspace_member,
    unbind_workspace,
    workspace_binding_preview,
)

__all__ = [
    "User",
    "_can_manage",
    "_disconnect_user_after_commit",
    "_grant_owner_workspace_admin",
    "_invitation_expires_at",
    "_issue_owner_setup_invitation",
    "_membership",
    "_pending_owner_invitations",
    "_remove_workspace_user",
    "_require_actor",
    "_require_workspace_admin",
    "_sync_member",
    "_sync_workspace_user",
    "accept_invitation",
    "add_member",
    "assign_workspace_member",
    "audit",
    "bind_workspace",
    "change_organization_lifecycle",
    "create_organization",
    "create_pending_team",
    "invite_member",
    "organization_snapshot",
    "provision_paid_team",
    "reassign_owner_setup",
    "reject_legacy_workspace_membership_mutation",
    "remove_member",
    "resend_owner_setup",
    "revoke_invitation",
    "team_occupied_seats",
    "transition_to_personal",
    "unassign_workspace_member",
    "unbind_workspace",
    "update_member",
    "update_organization",
    "workspace_binding_preview",
]
