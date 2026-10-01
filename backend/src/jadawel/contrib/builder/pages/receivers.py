from django.dispatch import receiver

from jadawel.contrib.builder.pages.last_viewed_types import (
    BuilderPageLastViewedItemType,
)
from jadawel.contrib.builder.pages.signals import page_deleted, page_loaded
from jadawel.core.last_viewed.handler import LastViewedHandler


@receiver(page_loaded)
def page_loaded_mark_last_viewed(sender, page, user, **kwargs):
    # The editor loads the shared page's elements on every builder visit, which
    # says nothing about what the user is looking at.
    if page.shared:
        return
    LastViewedHandler.schedule_mark_viewed(
        user, BuilderPageLastViewedItemType.type, page.id
    )


@receiver(page_deleted)
def page_deleted_forget_last_viewed(sender, builder, page_id, **kwargs):
    LastViewedHandler.delete_items(BuilderPageLastViewedItemType.type, [page_id])
