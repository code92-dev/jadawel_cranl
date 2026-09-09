# backend/src/jadawel/core/formula/parser/formula_validation_visitor.py

- DeferredValue · class · L20-L30 — class DeferredValue
- JadawelFormulaValidationVisitor · class · L33-L200 — class JadawelFormulaValidationVisitor(JadawelFormulaVisitor)
- __init__ · method · L39-L45 — def __init__( self, functions: "FunctionCollection", data_provider_type_registry: Optional["DataProviderTypeRegistry"] = None, )
- visitRoot · method · L47-L48 — def visitRoot(self, ctx: JadawelFormula.RootContext)
- visitStringLiteral · method · L50-L52 — def visitStringLiteral(self, ctx: JadawelFormula.StringLiteralContext): # noinspection PyTypeChecker
- visitBinaryOp · method · L54-L82 — def visitBinaryOp(self, ctx: JadawelFormula.BinaryOpContext)
- process_string · method · L84-L90 — def process_string(self, ctx)
- visitDecimalLiteral · method · L92-L93 — def visitDecimalLiteral(self, ctx: JadawelFormula.DecimalLiteralContext)
- visitBooleanLiteral · method · L95-L96 — def visitBooleanLiteral(self, ctx: JadawelFormula.BooleanLiteralContext)
- visitBrackets · method · L98-L99 — def visitBrackets(self, ctx: JadawelFormula.BracketsContext)
- visitIdentifier · method · L101-L102 — def visitIdentifier(self, ctx: JadawelFormula.IdentifierContext)
- visitIntegerLiteral · method · L104-L105 — def visitIntegerLiteral(self, ctx: JadawelFormula.IntegerLiteralContext)
- visitFieldByIdReference · method · L107-L108 — def visitFieldByIdReference(self, ctx: JadawelFormula.FieldByIdReferenceContext)
- visitLeftWhitespaceOrComments · method · L110-L113 — def visitLeftWhitespaceOrComments( self, ctx: JadawelFormula.LeftWhitespaceOrCommentsContext )
- visitRightWhitespaceOrComments · method · L115-L118 — def visitRightWhitespaceOrComments( self, ctx: JadawelFormula.RightWhitespaceOrCommentsContext )
- visitFieldReference · method · L120-L126 — def visitFieldReference(self, ctx: JadawelFormula.FieldReferenceContext)
- _parse_args_for_validation · method · L128-L155 — def _parse_args_for_validation( self, formula_function_type, accepted_args: List ) -> List
- visitFunctionCall · method · L157-L200 — def visitFunctionCall( self, ctx: JadawelFormula.FunctionCallContext, function_name: str = None )
