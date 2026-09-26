from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

ERROR_SANAD_NOT_ALLOWED = (
    "ERROR_SANAD_NOT_ALLOWED",
    HTTP_403_FORBIDDEN,
    "Sanad is only available to instance administrators.",
)

ERROR_SANAD_CHAT_DOES_NOT_EXIST = (
    "ERROR_SANAD_CHAT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested Sanad chat does not exist.",
)

ERROR_SANAD_NO_MODEL_AVAILABLE = (
    "ERROR_SANAD_NO_MODEL_AVAILABLE",
    HTTP_400_BAD_REQUEST,
    "No generative AI provider is configured on this instance.",
)

ERROR_SANAD_MODEL_NOT_AVAILABLE = (
    "ERROR_SANAD_MODEL_NOT_AVAILABLE",
    HTTP_400_BAD_REQUEST,
    "The requested model is not enabled on this instance.",
)

ERROR_SANAD_CHAT_BUSY = (
    "ERROR_SANAD_CHAT_BUSY",
    HTTP_409_CONFLICT,
    "Sanad is still answering, or waiting for an approval, in this chat.",
)

ERROR_SANAD_NOTHING_TO_APPROVE = (
    "ERROR_SANAD_NOTHING_TO_APPROVE",
    HTTP_400_BAD_REQUEST,
    "Every pending action needs exactly one decision, and none may be extra.",
)
