# backend/src/jadawel/core/formula/parser/parser.py

- JadawelFormulaErrorListener · class · L12-L22 — class JadawelFormulaErrorListener(ErrorListener)
- syntaxError · method · L19-L22 — def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e)
- get_token_stream_for_formula · function · L25-L30 — def get_token_stream_for_formula(formula: str) -> BufferedTokenStream
- get_parse_tree_for_formula · function · L33-L44 — def get_parse_tree_for_formula(formula: str)
- convert_string_literal_token_to_string · function · L48-L51 — def convert_string_literal_token_to_string(string_literal, is_single_q)
- convert_string_to_string_literal_token · function · L54-L57 — def convert_string_to_string_literal_token(string, is_single_q)
