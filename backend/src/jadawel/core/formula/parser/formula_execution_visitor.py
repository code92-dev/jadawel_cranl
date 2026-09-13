import re

from jadawel.core.formula import JadawelFormula, JadawelFormulaVisitor
from jadawel.core.formula.parser.exceptions import (
    FieldByIdReferencesAreDeprecated,
    FormulaFunctionTypeDoesNotExist,
    JadawelFormulaSyntaxError,
    UnknownOperator,
)
from jadawel.core.formula.types import (
    FormulaContext,
    FormulaFunction,
    FunctionCollection,
)


class JadawelFormulaExecutionVisitor(JadawelFormulaVisitor):
    def __init__(
        self,
        functions: FunctionCollection,
        context: FormulaContext,
    ):
        self.context = context
        self.functions = functions

    def visitRoot(self, ctx: JadawelFormula.RootContext):
        return ctx.expr().accept(self)

    def visitStringLiteral(self, ctx: JadawelFormula.StringLiteralContext):
        # noinspection PyTypeChecker
        return self.process_string(ctx)

    def visitDecimalLiteral(self, ctx: JadawelFormula.DecimalLiteralContext):
        return float(ctx.getText())

    def visitBooleanLiteral(self, ctx: JadawelFormula.BooleanLiteralContext):
        return ctx.TRUE() is not None

    def visitBrackets(self, ctx: JadawelFormula.BracketsContext):
        return ctx.expr().accept(self)

    def process_string(self, ctx):
        literal_without_outer_quotes = ctx.getText()[1:-1]
        if ctx.SINGLEQ_STRING_LITERAL() is not None:
            literal = re.sub(r"\\(['\\])", r"\1", literal_without_outer_quotes)
        else:
            literal = re.sub(r'\\(["\\])', r"\1", literal_without_outer_quotes)
        return literal

    def visitFunctionCall(self, ctx: JadawelFormula.FunctionCallContext):
        function_name = ctx.func_name().accept(self).lower()
        function_argument_expressions = ctx.expr()

        return self._do_func(function_argument_expressions, function_name)

    def _do_func(self, function_argument_expressions, function_name: str):
        args = [expr.accept(self) for expr in function_argument_expressions]
        formula_function_type = self._get_formula_function_type(function_name)
        args_parsed = formula_function_type.parse_args(args)
        return formula_function_type.execute(self.context, args_parsed)

    def _get_formula_function_type(self, function_name: str) -> FormulaFunction:
        try:
            return self.functions.get(function_name)
        except FormulaFunctionTypeDoesNotExist:
            raise JadawelFormulaSyntaxError(f"{function_name} is not a valid function")

    def visitBinaryOp(self, ctx: JadawelFormula.BinaryOpContext):
        if ctx.PLUS():
            op = "add"
        elif ctx.MINUS():
            op = "minus"
        elif ctx.SLASH():
            op = "divide"
        elif ctx.EQUAL():
            op = "equal"
        elif ctx.BANG_EQUAL():
            op = "not_equal"
        elif ctx.STAR():
            op = "multiply"
        elif ctx.GT():
            op = "greater_than"
        elif ctx.LT():
            op = "less_than"
        elif ctx.GTE():
            op = "greater_than_or_equal"
        elif ctx.LTE():
            op = "less_than_or_equal"
        elif ctx.AMP_AMP():
            op = "and"
        elif ctx.PIPE_PIPE():
            op = "or"
        else:
            raise UnknownOperator(ctx.getText())

        return self._do_func(ctx.expr(), op)

    def visitFunc_name(self, ctx: JadawelFormula.Func_nameContext):
        return ctx.getText()

    def visitIdentifier(self, ctx: JadawelFormula.IdentifierContext):
        return ctx.getText()

    def visitIntegerLiteral(self, ctx: JadawelFormula.IntegerLiteralContext):
        return int(ctx.getText())

    def visitFieldByIdReference(self, ctx: JadawelFormula.FieldByIdReferenceContext):
        raise FieldByIdReferencesAreDeprecated()

    def visitLeftWhitespaceOrComments(
        self, ctx: JadawelFormula.LeftWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)

    def visitRightWhitespaceOrComments(
        self, ctx: JadawelFormula.RightWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)
