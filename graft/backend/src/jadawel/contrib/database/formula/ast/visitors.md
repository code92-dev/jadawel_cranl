# backend/src/jadawel/contrib/database/formula/ast/visitors.py

- JadawelFormulaASTVisitor · class · L10-L39 — class JadawelFormulaASTVisitor(abc.ABC, Generic[Y, X])
- visit_string_literal · method · L12-L13 — def visit_string_literal(self, string_literal: "tree.JadawelStringLiteral[Y]") -> X
- visit_function_call · method · L16-L17 — def visit_function_call(self, function_call: "tree.JadawelFunctionCall[Y]") -> X
- visit_int_literal · method · L20-L21 — def visit_int_literal(self, int_literal: "tree.JadawelIntegerLiteral[Y]") -> X
- visit_field_reference · method · L24-L27 — def visit_field_reference( self, field_reference: "tree.JadawelFieldReference[Y]" ) -> X
- visit_decimal_literal · method · L30-L33 — def visit_decimal_literal( self, decimal_literal: "tree.JadawelDecimalLiteral[Y]" ) -> X
- visit_boolean_literal · method · L36-L39 — def visit_boolean_literal( self, boolean_literal: "tree.JadawelBooleanLiteral[Y]" ) -> X
