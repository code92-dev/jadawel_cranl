"""Secrets the fork must keep but never store in plain text.

A value is sealed with Fernet under a key derived from ``SECRET_KEY`` and a
purpose, so one purpose's ciphertext cannot be opened as another's, and rotating
``SECRET_KEY`` makes every sealed value unreadable (``unseal`` returns None).
"""

import base64
from typing import Optional

from django.conf import settings
from django.utils.crypto import salted_hmac

from cryptography.fernet import Fernet, InvalidToken


class Sealer:
    def __init__(self, key_salt: str, purpose: str):
        self.key_salt = key_salt
        self.purpose = purpose

    def _fernet(self) -> Fernet:
        key = salted_hmac(
            self.key_salt,
            self.purpose,
            secret=settings.SECRET_KEY,
            algorithm="sha256",
        ).digest()
        return Fernet(base64.urlsafe_b64encode(key))

    def seal(self, value: str) -> str:
        return self._fernet().encrypt(value.encode()).decode()

    def unseal(self, value: str) -> Optional[str]:
        """The plain value, or None when it was sealed under another SECRET_KEY."""

        try:
            return self._fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return None
