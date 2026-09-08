from rest_framework.exceptions import APIException


class ProviderUnavailable(APIException):
    status_code = 503
    default_detail = "payment_verification_unavailable"
    default_code = "payment_verification_unavailable"
