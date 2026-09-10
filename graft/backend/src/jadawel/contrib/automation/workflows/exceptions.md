# backend/src/jadawel/contrib/automation/workflows/exceptions.py

- AutomationWorkflowError · class · L4-L5 — class AutomationWorkflowError(AutomationError)
- AutomationWorkflowNotInAutomation · class · L8-L17 — class AutomationWorkflowNotInAutomation(AutomationWorkflowError)
- __init__ · method · L11-L17 — def __init__(self, workflow_id=None, *args, **kwargs)
- AutomationWorkflowDoesNotExist · class · L20-L23 — class AutomationWorkflowDoesNotExist(AutomationWorkflowError)
- AutomationWorkflowNotificationRecipientsInvalid · class · L26-L30 — class AutomationWorkflowNotificationRecipientsInvalid(AutomationWorkflowError)
- AutomationWorkflowBeforeRunError · class · L33-L34 — class AutomationWorkflowBeforeRunError(AutomationWorkflowError)
- AutomationWorkflowRateLimited · class · L37-L40 — class AutomationWorkflowRateLimited(AutomationWorkflowBeforeRunError)
- AutomationWorkflowTooManyErrors · class · L43-L46 — class AutomationWorkflowTooManyErrors(AutomationWorkflowBeforeRunError)
