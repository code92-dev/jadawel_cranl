# web-frontend/modules/core/formula/parser/formulaValidationVisitor.js

- JadawelFormulaValidationVisitor · class · L21-L177 — class JadawelFormulaValidationVisitor extends JadawelFormulaVisitor
- constructor · method · L26-L30 — constructor(functions, validationContext = {})
- visitRoot · method · L32-L34 — visitRoot(ctx)
- visitFieldReference · method · L36-L38 — visitFieldReference(ctx)
- visitStringLiteral · method · L40-L42 — visitStringLiteral(ctx)
- visitDecimalLiteral · method · L44-L46 — visitDecimalLiteral(ctx)
- visitBooleanLiteral · method · L48-L50 — visitBooleanLiteral(ctx)
- visitBrackets · method · L52-L54 — visitBrackets(ctx)
- visitIdentifier · method · L56-L58 — visitIdentifier(ctx)
- visitIntegerLiteral · method · L60-L62 — visitIntegerLiteral(ctx)
- visitLeftWhitespaceOrComments · method · L64-L66 — visitLeftWhitespaceOrComments(ctx)
- visitRightWhitespaceOrComments · method · L68-L70 — visitRightWhitespaceOrComments(ctx)
- visitBinaryOp · method · L72-L102 — visitBinaryOp(ctx)
- processString · method · L104-L113 — processString(ctx)
- _parseArgsForValidation · method · L122-L137 — _parseArgsForValidation(formulaFunctionType, acceptedArgs)
- visitFunctionCall · method · L142-L176 — visitFunctionCall(ctx, operatorFn = null)
