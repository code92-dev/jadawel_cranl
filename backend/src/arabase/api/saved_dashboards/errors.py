from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_502_BAD_GATEWAY,
)

ERROR_SAVED_DASHBOARD_DOES_NOT_EXIST = (
    "ERROR_SAVED_DASHBOARD_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The dashboard is not on your page.",
)

ERROR_SAVED_DASHBOARD_LINK_INVALID = (
    "ERROR_SAVED_DASHBOARD_LINK_INVALID",
    HTTP_400_BAD_REQUEST,
    "That is not the public link of a dashboard.",
)

ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED = (
    "ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED",
    HTTP_401_UNAUTHORIZED,
    "The dashboard is password protected.",
)

ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT = (
    "ERROR_SAVED_DASHBOARD_PASSWORD_INCORRECT",
    HTTP_401_UNAUTHORIZED,
    "The password is incorrect.",
)

ERROR_SAVED_DASHBOARD_UNAVAILABLE = (
    "ERROR_SAVED_DASHBOARD_UNAVAILABLE",
    HTTP_404_NOT_FOUND,
    "The dashboard is no longer shared, or you no longer have access to it.",
)

ERROR_SAVED_DASHBOARD_UNREACHABLE = (
    "ERROR_SAVED_DASHBOARD_UNREACHABLE",
    HTTP_502_BAD_GATEWAY,
    "The server the dashboard is on could not be reached.",
)

ERROR_SAVED_DASHBOARD_HAS_NO_PASSWORD = (
    "ERROR_SAVED_DASHBOARD_HAS_NO_PASSWORD",
    HTTP_400_BAD_REQUEST,
    "A dashboard from your workspace takes no password.",
)

ERROR_SAVED_DASHBOARD_DATA_FAILED = (
    "ERROR_SAVED_DASHBOARD_DATA_FAILED",
    HTTP_502_BAD_GATEWAY,
    "The other server could not load this data.",
)
