# web-frontend/modules/core/formula/parser/errors.js

- JadawelFormulaParserError · class · L1-L9 — class JadawelFormulaParserError extends Error
- constructor · method · L2-L8 — constructor(offendingSymbol, line, character, message)
- UnknownOperatorError · class · L11-L16 — class UnknownOperatorError extends Error
- constructor · method · L12-L15 — constructor(operatorName)
- BaseHumanReadableError · class · L23-L25 — class BaseHumanReadableError extends Error
- InvalidNumberOfArguments · class · L27-L56 — class InvalidNumberOfArguments extends BaseHumanReadableError
- constructor · method · L28-L34 — constructor(formulaFunctionType, minArgs, maxArgs = null)
- getMessage · method · L36-L55 — getMessage()
- InvalidFormulaType · class · L58-L63 — class InvalidFormulaType extends BaseHumanReadableError
- constructor · method · L59-L62 — constructor(message)
- InvalidFormulaArgumentType · class · L65-L71 — class InvalidFormulaArgumentType extends BaseHumanReadableError
- constructor · method · L66-L70 — constructor(formulaFunctionType, arg)
- InvalidFormulaArgument · class · L73-L79 — class InvalidFormulaArgument extends BaseHumanReadableError
- constructor · method · L74-L78 — constructor(arg, message)
