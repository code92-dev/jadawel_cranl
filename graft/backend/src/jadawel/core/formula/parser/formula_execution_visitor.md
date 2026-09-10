# backend/src/jadawel/core/formula/parser/formula_execution_visitor.py

- JadawelFormulaExecutionVisitor · class · L15-L116 — class JadawelFormulaExecutionVisitor(JadawelFormulaVisitor)
- __init__ · method · L16-L22 — def __init__( self, functions: FunctionCollection, context: FormulaContext, )
- visitRoot · method · L24-L25 — def visitRoot(self, ctx: JadawelFormula.RootContext)
- visitStringLiteral · method · L27-L29 — def visitStringLiteral(self, ctx: JadawelFormula.StringLiteralContext): # noinspection PyTypeChecker
- visitDecimalLiteral · method · L31-L32 — def visitDecimalLiteral(self, ctx: JadawelFormula.DecimalLiteralContext)
- visitBooleanLiteral · method · L34-L35 — def visitBooleanLiteral(self, ctx: JadawelFormula.BooleanLiteralContext)
- visitBrackets · method · L37-L38 — def visitBrackets(self, ctx: JadawelFormula.BracketsContext)
- process_string · method · L40-L46 — def process_string(self, ctx)
- visitFunctionCall · method · L48-L52 — def visitFunctionCall(self, ctx: JadawelFormula.FunctionCallContext)
- _do_func · method · L54-L58 — def _do_func(self, function_argument_expressions, function_name: str)
- _get_formula_function_type · method · L60-L64 — def _get_formula_function_type(self, function_name: str) -> FormulaFunction
- visitBinaryOp · method · L66-L94 — def visitBinaryOp(self, ctx: JadawelFormula.BinaryOpContext)
- visitFunc_name · method · L96-L97 — def visitFunc_name(self, ctx: JadawelFormula.Func_nameContext)
- visitIdentifier · method · L99-L100 — def visitIdentifier(self, ctx: JadawelFormula.IdentifierContext)
- visitIntegerLiteral · method · L102-L103 — def visitIntegerLiteral(self, ctx: JadawelFormula.IntegerLiteralContext)
- visitFieldByIdReference · method · L105-L106 — def visitFieldByIdReference(self, ctx: JadawelFormula.FieldByIdReferenceContext)
- visitLeftWhitespaceOrComments · method · L108-L111 — def visitLeftWhitespaceOrComments( self, ctx: JadawelFormula.LeftWhitespaceOrCommentsContext )
- visitRightWhitespaceOrComments · method · L113-L116 — def visitRightWhitespaceOrComments( self, ctx: JadawelFormula.RightWhitespaceOrCommentsContext )
