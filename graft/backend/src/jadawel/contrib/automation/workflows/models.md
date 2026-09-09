# backend/src/jadawel/contrib/automation/workflows/models.py

- AutomationWorkflowTrashManager · class · L27-L43 — class AutomationWorkflowTrashManager(models.Manager)
- get_queryset · method · L34-L43 — def get_queryset(self)
- AutomationWorkflow · class · L46-L205 — class AutomationWorkflow( HierarchicalModelMixin, TrashableModelMixin, CreatedAndUpdatedOnMixin, OrderableMixin, )
- Meta · class · L93-L94 — class Meta
- get_parent · method · L96-L97 — def get_parent(self)
- get_last_order · method · L100-L102 — def get_last_order(cls, automation: "Automation")
- is_original · method · L104-L109 — def is_original(self) -> bool
- get_original · method · L111-L127 — def get_original(self) -> "AutomationWorkflow"
- get_trigger · method · L129-L134 — def get_trigger(self) -> "AutomationTriggerNode"
- can_immediately_be_tested · method · L136-L142 — def can_immediately_be_tested(self)
- get_graph · method · L144-L158 — def get_graph(self)
- is_published · method · L161-L172 — def is_published(self) -> bool
- print · method · L174-L187 — def print(self, message=None, original=False)
- assert_reference · method · L189-L205 — def assert_reference(self, reference)
- DuplicateAutomationWorkflowJob · class · L208-L225 — class DuplicateAutomationWorkflowJob( JobWithUserIpAddress, JobWithWebsocketId, JobWithUndoRedoIds, Job )
- PublishAutomationWorkflowJob · class · L228-L233 — class PublishAutomationWorkflowJob(JobWithUserIpAddress, Job)
