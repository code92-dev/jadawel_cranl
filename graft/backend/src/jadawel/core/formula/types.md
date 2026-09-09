# backend/src/jadawel/core/formula/types.py

- FormulaContext · class · L11-L45 — class FormulaContext(ABC)
- __init__ · method · L12-L22 — def __init__(self)
- add_call · method · L24-L34 — def add_call(self, call_id: Any)
- reset_call_stack · method · L36-L39 — def reset_call_stack(self)
- __getitem__ · method · L42-L45 — def __getitem__(self, key: str) -> Any
- FunctionCollection · class · L48-L55 — class FunctionCollection(ABC)
- get · method · L50-L55 — def get(self, name: str)
- FormulaFunction · class · L58-L71 — class FormulaFunction(ABC)
- validate_args · method · L60-L61 — def validate_args(self, args: FormulaArgs)
- parse_args · method · L64-L67 — def parse_args(self, args: FormulaArgs) -> FormulaArgs
- execute · method · L70-L71 — def execute(self, context: FormulaContext, args: FormulaArgs) -> Any
- JadawelFormulaObject · class · L80-L103 — class JadawelFormulaObject(TypedDict)
- create · method · L86-L92 — def create( cls, formula: str = "", mode: JadawelFormulaMode = JADAWEL_FORMULA_MODE_SIMPLE, version: str = "0.1", ) -> "JadawelFormulaObject"
- to_formula · method · L95-L103 — def to_formula(cls, value) -> "JadawelFormulaObject"
- JadawelFormulaMinified · class · L106-L109 — class JadawelFormulaMinified(TypedDict)
