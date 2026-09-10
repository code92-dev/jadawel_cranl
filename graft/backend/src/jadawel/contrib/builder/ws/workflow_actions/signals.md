# backend/src/jadawel/contrib/builder/ws/workflow_actions/signals.py

- workflow_action_created · function · L26-L49 — def workflow_action_created( sender, workflow_action: WorkflowAction, user: AbstractUser, before_id=None, **kwargs, )
- workflow_action_updated · function · L53-L74 — def workflow_action_updated( sender, workflow_action: WorkflowAction, user: AbstractUser, **kwargs, )
- workflow_action_deleted · function · L78-L98 — def workflow_action_deleted( sender, workflow_action_id: int, page: Page, user: AbstractUser, **kwargs, )
