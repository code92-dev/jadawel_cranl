# backend/src/jadawel/contrib/database/formula/types/type_checker.py

- SingleArgumentTypeChecker · class · L14-L29 — class SingleArgumentTypeChecker(abc.ABC)
- check · method · L16-L21 — def check( self, arg_index: int, typed_expression_to_check: "JadawelExpression[JadawelFormulaType]", ) -> bool
- invalid_message · method · L24-L29 — def invalid_message( self, arg_index: int, type_which_failed_check: "JadawelExpression[JadawelFormulaType]", ) -> str
- MustBeManyExprChecker · class · L32-L66 — class MustBeManyExprChecker(SingleArgumentTypeChecker)
- __init__ · method · L40-L41 — def __init__(self, *formula_types: Type[JadawelFormulaType])
- check · method · L43-L51 — def check( self, arg_index: int, typed_expression_to_check: "JadawelExpression[JadawelFormulaType]", ) -> bool
- _expr_is_valid_type · method · L53-L54 — def _expr_is_valid_type(self, typed_expression_to_check)
- invalid_message · method · L56-L66 — def invalid_message( self, arg_index: int, typed_expression_to_check: "JadawelExpression[JadawelFormulaType]", ) -> str
