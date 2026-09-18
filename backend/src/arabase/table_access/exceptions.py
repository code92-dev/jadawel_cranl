class TableGrantDoesNotExist(Exception):
    """Raised when a grant is addressed that is not there (any more)."""


class TableNotInWorkspace(Exception):
    """Raised when a grant would point at a table outside the workspace."""


# An organization-managed workspace refuses guests too, but that rejection is
# core's: `CoreHandler.create_workspace_invitation` calls the organizations
# plugin's `validate_workspace_membership_mutation`, which raises
# `PermissionDenied` before any grant is written. No exception of our own is
# needed for it.
