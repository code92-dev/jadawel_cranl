from typing import Any
from urllib.parse import quote

import requests

from jadawel_billing.errors import ProviderUnavailable


class MoyasarClient:
    """Small server-only client for the Moyasar payment lookup endpoint."""

    base_url = "https://api.moyasar.com/v1/payments"

    def __init__(self, *, secret_key: str, mode: str) -> None:
        if not secret_key.startswith(f"sk_{mode}_"):
            raise ProviderUnavailable()
        self.secret_key = secret_key

    def fetch(self, payment_id: Any) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/{quote(str(payment_id), safe='')}",
                auth=(self.secret_key, ""),
                timeout=(5, 15),
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise ProviderUnavailable()
            payment = response.json()
            if not isinstance(payment, dict):
                raise ProviderUnavailable()
            return payment
        except (requests.RequestException, ValueError) as exc:
            raise ProviderUnavailable() from exc
