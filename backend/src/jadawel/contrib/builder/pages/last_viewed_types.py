from typing import Iterable

from django.db.models import QuerySet

from jadawel.contrib.builder.operations import ListPagesBuilderOperationType
from jadawel.contrib.builder.pages.models import Page
from jadawel.core.registries import LastViewedItemType


class BuilderPageLastViewedItemType(LastViewedItemType):
    type = "builder_page"
    model_class = Page
    list_operation_type = ListPagesBuilderOperationType.type

    def get_visible_queryset(self) -> QuerySet:
        # The shared page is loaded on every builder visit, so it never counts as
        # viewed, whichever path leads here.
        return Page.objects_without_shared.filter(builder__trashed=False)

    def get_queryset_for_user(self, user_id: int) -> QuerySet:
        return (
            self.get_visible_queryset()
            .select_related("builder")
            .filter(
                builder__workspace__trashed=False,
                builder__workspace__workspaceuser__user_id=user_id,
            )
        )

    def get_application_id(self, instance: Page) -> int:
        return instance.builder_id

    def get_workspace_id(self, instance: Page) -> int:
        return instance.builder.workspace_id

    def get_item_ids_of_permanently_deleted(
        self, trash_item_type: str, trash_item
    ) -> Iterable[int]:
        # Jadawel fork: pages are not trashable here, a deleted page is gone at
        # once and `page_deleted_forget_last_viewed` forgets it.
        return []
