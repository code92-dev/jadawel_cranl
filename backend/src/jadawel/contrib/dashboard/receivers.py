from django.dispatch import receiver

from jadawel.contrib.dashboard.last_viewed_types import (
    DashboardLastViewedItemType,
)
from jadawel.contrib.dashboard.signals import dashboard_loaded
from jadawel.core.last_viewed.handler import LastViewedHandler


@receiver(dashboard_loaded)
def dashboard_loaded_mark_last_viewed(sender, dashboard_id, user, **kwargs):
    LastViewedHandler.schedule_mark_viewed(
        user, DashboardLastViewedItemType.type, dashboard_id
    )
