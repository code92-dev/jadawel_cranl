from django.conf import settings

from celery_singleton import Singleton

from jadawel.config.celery import app

from .action.tasks import cleanup_old_actions, setup_periodic_action_tasks
from .last_viewed.tasks import (
    clean_up_stale_last_viewed_items,
    mark_item_viewed,
    setup_periodic_last_viewed_tasks,
)
from .snapshots.tasks import delete_expired_snapshots
from .telemetry.tasks import initialize_otel
from .trash.tasks import (
    mark_old_trash_for_permanent_deletion,
    permanently_delete_marked_trash,
    setup_period_trash_tasks,
)
from .usage.tasks import run_calculate_storage
from .user.tasks import check_pending_account_deletion


@app.task(
    name="jadawel.core.tasks.sync_templates_task",
    base=Singleton,
    raise_on_duplicate=False,
    bind=True,
    queue="export",
    time_limit=settings.JADAWEL_SYNC_TEMPLATES_TIME_LIMIT,
    lock_expiry=settings.JADAWEL_SYNC_TEMPLATES_TIME_LIMIT,
)
def sync_templates_task(self):
    from jadawel.core.handler import CoreHandler

    CoreHandler().sync_templates(pattern=settings.JADAWEL_SYNC_TEMPLATES_PATTERN)


__all__ = [
    "permanently_delete_marked_trash",
    "mark_old_trash_for_permanent_deletion",
    "setup_period_trash_tasks",
    "cleanup_old_actions",
    "setup_periodic_action_tasks",
    "sync_templates_task",
    "run_calculate_storage",
    "check_pending_account_deletion",
    "delete_expired_snapshots",
    "initialize_otel",
    "mark_item_viewed",
    "clean_up_stale_last_viewed_items",
    "setup_periodic_last_viewed_tasks",
]
