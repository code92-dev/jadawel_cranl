# backend/src/jadawel/core/formula/registries.py

- RuntimeFormulaFunction · class · L21-L137 — class RuntimeFormulaFunction(ABC, Instance): # The minimum number of arguments that the function expects. This value # will only be used if `args` is not defined.
- type · method · L29-L34 — def type(cls) -> str
- args · method · L37-L45 — def args(self) -> Optional[List[JadawelRuntimeFormulaArgumentType]]
- num_args · method · L48-L55 — def num_args(self)
- execute · method · L58-L65 — def execute(self, context: FormulaContext, args: FormulaArgs) -> Any
- validate_args · method · L67-L84 — def validate_args( self, args: FormulaArgs, validation_context: Optional[Dict[str, Any]] = None, )
- validate_number_of_args · method · L86-L100 — def validate_number_of_args(self, args: FormulaArgs) -> bool
- validate_type_of_args · method · L102-L121 — def validate_type_of_args(self, args: FormulaArgs) -> Optional[FormulaArg]
- parse_args · method · L123-L137 — def parse_args(self, args: FormulaArgs) -> FormulaArgs
- JadawelRuntimeFormulaFunctionRegistry · class · L140-L144 — class JadawelRuntimeFormulaFunctionRegistry( Registry[RuntimeFormulaFunction], FunctionCollection )
- DataProviderType · class · L147-L215 — class DataProviderType( Instance, ABC, )
- get_data_chunk · method · L161-L165 — def get_data_chunk(self, dispatch_context: DispatchContext, path: List[str])
- import_path · method · L167-L178 — def import_path( self, path: List[str], id_mapping: Dict[int, int], **kwargs ) -> List[str]
- is_valid · method · L180-L185 — def is_valid(self, path: List[str]) -> bool
- extract_properties · method · L187-L201 — def extract_properties( self, path: List[str], **kwargs, ) -> Dict[str, List[str]]
- post_dispatch · method · L203-L215 — def post_dispatch( self, dispatch_context: DispatchContext, workflow_action: WorkflowAction, dispatch_result: DispatchResult, ) -> None
- DataProviderTypeRegistry · class · L221-L228 — class DataProviderTypeRegistry( Registry[DataProviderTypeSubClass], )
