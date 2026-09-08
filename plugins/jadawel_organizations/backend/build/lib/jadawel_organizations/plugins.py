from typing import Any

from django.urls import include, path
from jadawel.core.registries import Plugin


class OrganizationsPlugin(Plugin):
    type = "jadawel_organizations"

    def validate_workspace_membership_mutation(
        self, actor: Any, workspace: Any, operation: str, target_user: Any = None
    ) -> None:
        from .handlers import reject_legacy_workspace_membership_mutation

        reject_legacy_workspace_membership_mutation(
            actor, workspace, operation, target_user=target_user
        )

    def get_api_urls(self) -> list[Any]:
        return [
            path(
                "organizations/",
                include("jadawel_organizations.api.urls", namespace=self.type),
            )
        ]
