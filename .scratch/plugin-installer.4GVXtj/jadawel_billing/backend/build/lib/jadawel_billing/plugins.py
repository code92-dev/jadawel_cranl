from typing import Any

from django.urls import include, path
from jadawel.core.registries import Plugin


class BillingPlugin(Plugin):
    type = "jadawel_billing"

    def get_api_urls(self) -> list[Any]:
        return [
            path(
                "billing/",
                include("jadawel_billing.api.urls", namespace=self.type),
            )
        ]
