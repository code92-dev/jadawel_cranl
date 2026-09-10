# backend/src/jadawel/core/workflow_actions/registries.py

- WorkflowActionType · class · L18-L98 — class WorkflowActionType( InstanceWithFormulaMixin, EasyImportExportMixin, ModelInstanceMixin, Instance, ABC, )
- serialize_property · method · L27-L49 — def serialize_property( self, workflow_action: WorkflowAction, prop_name: str, files_zip=None, storage=None, cache=None, )
- prepare_values · method · L51-L70 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser, instance: WorkflowAction = None, )
- get_pytest_params · method · L73-L80 — def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]
- get_pytest_params_serialized · method · L82-L90 — def get_pytest_params_serialized( self, pytest_params: Dict[str, Any] ) -> Dict[str, Any]
- dispatch · method · L93-L98 — def dispatch( self, workflow_action: "WorkflowAction", dispatch_context: DispatchContext ) -> DispatchResult
