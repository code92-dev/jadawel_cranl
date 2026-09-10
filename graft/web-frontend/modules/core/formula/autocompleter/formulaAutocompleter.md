# web-frontend/modules/core/formula/autocompleter/formulaAutocompleter.js

- _countRemainingOpenBrackets · function · L21-L32 — function _countRemainingOpenBrackets(i, stop, stream, numOpenBrackets)
- _calculateAutocompleteRangeAndType · function · L46-L125 — function _calculateAutocompleteRangeAndType(formula, cursorPosition)
- _calculateFunctionAutocompleteResult · function · L144-L184 — function _calculateFunctionAutocompleteResult( functionCandidate, cursorPosition, autocompleteStartPosition, autocompleteEndPosition, tokenEndPosition, insideFunctionRef )
- _isCursorAtCorrectLocationInFieldRefToAutocomplete · function · L196-L213 — function _isCursorAtCorrectLocationInFieldRefToAutocomplete( innerFieldRefText, cursorPosition, autocompleteEndPosition )
- _calculateFieldAutocompleteResult · function · L241-L305 — function _calculateFieldAutocompleteResult( formula, autocompleteStartPosition, autocompleteEndPosition, cursorPosition, fieldCandidate, thereIsHangingOpenBracketAtCursor, insideFieldRef )
- _calculateAutocompleteLocationAndText · function · L332-L377 — function _calculateAutocompleteLocationAndText( formula, cursorPosition, functionCandidate, fieldCandidate )
- _fieldNameToStringLiteral · function · L379-L383 — function _fieldNameToStringLiteral(doubleQuote, fieldName)
- autocompleteFormula · function · L399-L427 — function autocompleteFormula( formula, startingCursorLocation, functionCandidate, fieldCandidate )
- _filterFieldsByStringLiteral · function · L429-L442 — function _filterFieldsByStringLiteral(tokenTextUptoCursor, fields)
- calculateFilteredFunctionsAndFieldsBasedOnCursorLocation · function · L460-L494 — function calculateFilteredFunctionsAndFieldsBasedOnCursorLocation( formula, cursorLocation, fields, functions )
