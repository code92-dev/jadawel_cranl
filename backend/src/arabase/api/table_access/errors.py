from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_TABLE_NOT_IN_WORKSPACE = (
    "ERROR_TABLE_NOT_IN_WORKSPACE",
    HTTP_400_BAD_REQUEST,
    "Every table of a guest grant must belong to the workspace of the invitation.",
)

ERROR_TABLE_GRANT_DOES_NOT_EXIST = (
    "ERROR_TABLE_GRANT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested guest membership does not exist in this workspace.",
)
