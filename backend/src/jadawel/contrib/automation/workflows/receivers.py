from django.dispatch import receiver

from jadawel.contrib.automation.workflows.last_viewed_types import (
    AutomationWorkflowLastViewedItemType,
)
from jadawel.contrib.automation.workflows.signals import automation_workflow_loaded
from jadawel.core.last_viewed.handler import LastViewedHandler


@receiver(automation_workflow_loaded)
def automation_workflow_loaded_mark_last_viewed(sender, workflow, user, **kwargs):
    LastViewedHandler.schedule_mark_viewed(
        user, AutomationWorkflowLastViewedItemType.type, workflow.id
    )
