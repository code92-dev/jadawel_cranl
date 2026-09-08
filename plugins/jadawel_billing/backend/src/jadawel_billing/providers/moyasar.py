from typing import Any
from urllib.parse import quote

import requests

from jadawel_billing.errors import ProviderUnavailable


class MoyasarClient:
    """Small server-only client for the Moyasar payment lookup endpoint."""

    base_url = "https://api.moyasar.com/v1/payments"
    tokens_url = "https://api.moyasar.com/v1/tokens"

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

    def health(self) -> dict[str, Any]:
        """Check provider reachability without exposing payment data.

        Listing a single payment is a read-only authenticated request.  The
        response is reduced to a safe status so the admin API never returns
        provider payloads or credentials.
        """
        try:
            response = requests.get(
                self.base_url,
                auth=(self.secret_key, ""),
                params={"limit": 1},
                timeout=(5, 15),
                allow_redirects=False,
            )
        except requests.RequestException:
            return {"status": "unreachable", "reachable": False}
        if response.status_code == 200:
            return {"status": "ok", "reachable": True}
        if response.status_code in (401, 403):
            return {"status": "invalid_credentials", "reachable": True}
        return {"status": "provider_error", "reachable": True}

    def fetch_token(self, token_id: str) -> dict[str, Any]:
        """Fetch a token with the secret key before it can be stored for reuse."""
        try:
            response = requests.get(
                f"{self.tokens_url}/{quote(str(token_id), safe='')}",
                auth=(self.secret_key, ""),
                timeout=(5, 15),
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise ProviderUnavailable()
            token = response.json()
            if not isinstance(token, dict) or token.get("id") != token_id:
                raise ProviderUnavailable()
            return token
        except (requests.RequestException, ValueError) as exc:
            raise ProviderUnavailable() from exc

    def charge(
        self,
        *,
        amount: int,
        currency: str,
        token: str,
        given_id: Any,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            response = requests.post(
                self.base_url,
                auth=(self.secret_key, ""),
                json={
                    "amount": amount,
                    "currency": currency,
                    "source": {"type": "token", "token": token},
                    "given_id": str(given_id),
                    "metadata": metadata,
                },
                timeout=(5, 15),
                allow_redirects=False,
            )
            if response.status_code not in (200, 201):
                raise ProviderUnavailable()
            payment = response.json()
            if not isinstance(payment, dict):
                raise ProviderUnavailable()
            return payment
        except (requests.RequestException, ValueError) as exc:
            raise ProviderUnavailable() from exc

    def refund(self, payment_id: str, amount: int) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/{quote(str(payment_id), safe='')}/refund",
                auth=(self.secret_key, ""),
                json={"amount": amount},
                timeout=(5, 15),
                allow_redirects=False,
            )
            if response.status_code not in (200, 201):
                raise ProviderUnavailable()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ProviderUnavailable()
            return payload
        except (requests.RequestException, ValueError) as exc:
            raise ProviderUnavailable() from exc
