# backend/src/jadawel/contrib/builder/workflow_actions/registries.py

- BuilderWorkflowActionType · class · L27-L164 — class BuilderWorkflowActionType( WorkflowActionType, PublicCustomFieldsInstanceMixin, BuilderInstanceWithFormulaMixin )
- prepare_values · method · L35-L46 — def prepare_values( self, values: Dict[str, Any], user: AbstractUser, instance: BuilderWorkflowAction = None, )
- create_instance_from_serialized · method · L48-L79 — def create_instance_from_serialized( self, serialized_values: Dict[str, Any], id_mapping, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict[str, any]] = None, **kwargs, ) -> Type[BuilderWorkflowAction]
- deserialize_property · method · L81-L116 — def deserialize_property( self, prop_name: str, value: Any, id_mapping: Dict[str, Any], files_zip=None, storage=None, cache=None, **kwargs, ) -> Any
- import_serialized · method · L118-L157 — def import_serialized( self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict[str, Dict[int, int]], files_zip=None, storage=None, cache: Dict[str, Any] | None = None, **kwargs, ) -> Any
- dispatch · method · L159-L164 — def dispatch( self, workflow_action: WorkflowAction, dispatch_context: "BuilderDispatchContext", ) -> DispatchResult
- BuilderWorkflowActionTypeRegistry · class · L167-L174 — class BuilderWorkflowActionTypeRegistry( Registry, ModelRegistryMixin, CustomFieldsRegistryMixin )
