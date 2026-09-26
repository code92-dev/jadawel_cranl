from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_HTML_PAGE_DOES_NOT_EXIST = (
    "ERROR_HTML_PAGE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested page view does not exist.",
)

ERROR_HTML_PAGE_TOO_LARGE = (
    "ERROR_HTML_PAGE_TOO_LARGE",
    HTTP_400_BAD_REQUEST,
    "{e}",
)
