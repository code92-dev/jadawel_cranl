"""Shared constants for the database views layer."""

# Default number of group-by groups per page. Lives in the views layer so the handler
# and the API serializers can share it without the handler importing from the API layer.
GROUP_BY_DATA_DEFAULT_LIMIT = 40

# Maximum number of group-bys a view may have. Mirrored by ``MAX_GROUP_BYS`` in
# ``web-frontend/modules/database/constants.js``. Views that already hold more (created
# through the API before the cap, or by an import) keep working; only adding a new one
# beyond the cap is rejected.
MAX_GROUP_BYS = 5
