# backend/src/jadawel/contrib/builder/formula_property_extractor.py

- FormulaFieldVisitor · class · L21-L86 — class FormulaFieldVisitor(JadawelFormulaImporter)
- __init__ · method · L26-L32 — def __init__(self, **kwargs)
- get_data_provider_type_registry · method · L34-L35 — def get_data_provider_type_registry(self)
- visit · method · L37-L47 — def visit(self, tree: Tree) -> Set[str]
- visitFunctionCall · method · L49-L83 — def visitFunctionCall(self, ctx: JadawelFormula.FunctionCallContext)
- visitBinaryOp · method · L85-L86 — def visitBinaryOp(self, ctx: JadawelFormula.BinaryOpContext)
- get_element_property_names · function · L89-L114 — def get_element_property_names( elements: List[Element], element_map: Dict[str, Element], ) -> Dict[str, Dict[int, List[str]]]
- get_workflow_action_property_names · function · L117-L157 — def get_workflow_action_property_names( workflow_actions: List["WorkflowAction"], element_map: Dict[str, Element], ) -> Dict[str, Dict[int, List[str]]]
- get_data_source_property_names · function · L160-L180 — def get_data_source_property_names( data_sources: List["DataSource"], ) -> Dict[str, Dict[int, List[str]]]
- get_builder_used_property_names · function · L183-L250 — def get_builder_used_property_names( user: UserSourceUser, builder: "Builder" ) -> Dict[str, Dict[int, List[str]]]
