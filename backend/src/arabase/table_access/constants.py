"""Shared constants for table-scoped guest access.

Kept in their own module so the permission manager, the handler and the API can
import them without importing each other.
"""

# A fourth value for the existing ``WorkspaceUser.permissions`` /
# ``WorkspaceInvitation.permissions`` CharField, alongside core's ADMIN and
# MEMBER and this fork's VIEWER. The field has no ``choices`` and the API
# serializer does not constrain it, so adding a role needs no migration — the
# same trick ``arabase.permissions.viewer_role`` documents.
WORKSPACE_USER_PERMISSION_GUEST = "GUEST"
