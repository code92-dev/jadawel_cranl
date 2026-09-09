# backend/src/jadawel/contrib/automation/workflows/ws/signals.py

- workflow_created · function · L35-L50 — def workflow_created( sender, workflow: AutomationWorkflow, user: AbstractUser, **kwargs )
- workflow_deleted · function · L54-L70 — def workflow_deleted( sender, automation: Automation, workflow_id: int, user: AbstractUser, **kwargs )
- workflow_updated · function · L74-L89 — def workflow_updated( sender, workflow: AutomationWorkflow, user: AbstractUser, **kwargs )
- workflow_published · function · L93-L109 — def workflow_published( sender, workflow: AutomationWorkflow, user: AbstractUser, **kwargs )
- workflow_reordered · function · L113-L130 — def workflow_reordered( sender, automation: Automation, order: List[int], user: AbstractUser, **kwargs ): # Hashing all values here to not expose real ids of workflows a user # might not have access to
- workflow_dispatch_started · function · L134-L149 — def workflow_dispatch_started(sender, workflow_history, **kwargs)
- workflow_dispatch_done · function · L153-L168 — def workflow_dispatch_done(sender, workflow_history, **kwargs)
