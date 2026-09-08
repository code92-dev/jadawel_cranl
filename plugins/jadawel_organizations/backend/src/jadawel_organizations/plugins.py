from typing import Any

from django.urls import include, path
from jadawel.core.registries import Plugin


class OrganizationsPlugin(Plugin):
    type = "jadawel_organizations"

    def get_api_urls(self) -> list[Any]:
        return [
            path(
                "organizations/",
                include("jadawel_organizations.api.urls", namespace=self.type),
            )
        ]
