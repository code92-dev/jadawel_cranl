from django.db.models import QuerySet

from jadawel.contrib.dashboard.models import Dashboard
from jadawel.core.operations import ListApplicationsWorkspaceOperationType
from jadawel.core.registries import LastViewedItemType


class DashboardLastViewedItemType(LastViewedItemType):
    """
    A dashboard has no sub pages, so the application itself is the leaf. Its rows
    are removed by the foreign key cascade when the application is deleted.
    """

    type = "dashboard"
    model_class = Dashboard
    list_operation_type = ListApplicationsWorkspaceOperationType.type

    def get_visible_queryset(self) -> QuerySet:
        return Dashboard.objects.all()

    def get_queryset_for_user(self, user_id: int) -> QuerySet:
        return self.get_visible_queryset().filter(
            workspace__trashed=False, workspace__workspaceuser__user_id=user_id
        )

    def get_application_id(self, instance: Dashboard) -> int:
        return instance.id

    def get_workspace_id(self, instance: Dashboard) -> int:
        return instance.workspace_id
