"""
Backend consumer of the shared cross-runtime formula parity matrix.

Every case in ``tests/cases/runtime_formula_parity.json`` is executed through
the real backend formula stack — parser, runtime registry and execution
visitor — exactly as a saved formula runs at runtime. The same matrix is
executed by the frontend through its own parser and execution visitor in
``web-frontend/test/unit/formula/runtimeFormulaParity.spec.js``; a case may
only be changed together with its frontend outcome, never on one side alone.

A case succeeds when the visited result equals the declared JSON value (with
``duration_seconds`` / ``datetime_iso`` / ``array_length`` normalizing
timedelta, datetime and exact-boundary range results to JSON-comparable
shapes), and fails with category ``invalid_argument`` when the same expression
raises in the other runtime too. One runtime returning ``null`` where the
other raises is a parity failure and shows up as a failing case here.
"""

from datetime import datetime, timedelta, timezone

from django.core.exceptions import ValidationError

import pytest

from jadawel.core.formula import JadawelFormulaSyntaxError
from jadawel.core.formula.parser.exceptions import JadawelFormulaException
from jadawel.core.formula.parser.formula_execution_visitor import (
    JadawelFormulaExecutionVisitor,
)
from jadawel.core.formula.parser.parser import get_parse_tree_for_formula
from jadawel.core.formula.registries import formula_runtime_function_registry
from jadawel.test_utils.helpers import load_test_cases

TEST_DATA = load_test_cases("runtime_formula_parity")

PARITY_CASES = TEST_DATA["PARITY_CASES"]


def execute_formula_through_visitor(formula: str, context):
    tree = get_parse_tree_for_formula(formula)
    visitor = JadawelFormulaExecutionVisitor(formula_runtime_function_registry, context)
    return visitor.visit(tree)


def normalize_result(case, result):
    if "array_length" in case:
        return len(result)
    if "duration_seconds" in case:
        assert isinstance(result, timedelta)
        return result.total_seconds()
    if "datetime_iso" in case:
        assert isinstance(result, datetime)
        return result.isoformat(timespec="seconds")
    if "datetime_utc" in case:
        assert isinstance(result, datetime)
        # Offset-bearing inputs are compared as UTC instants, so the two
        # runtimes agree regardless of the test machine's timezone.
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case", PARITY_CASES, ids=[case["formula"] for case in PARITY_CASES]
)
def test_formula_parity_case(case, settings):
    # The boundary cases in the matrix are expressed against the documented
    # default maximum; pin it so a developer machine with an override in
    # .env.local cannot flip the shared contract.
    settings.FORMULA_RANGE_MAX_ITEMS = 10000

    formula = case["formula"]
    context = case.get("context", {})
    if "error" in case:
        with pytest.raises(
            (
                JadawelFormulaSyntaxError,
                JadawelFormulaException,
                ValidationError,
                ValueError,
            )
        ):
            execute_formula_through_visitor(formula, context)
        return

    result = execute_formula_through_visitor(formula, context)
    assert normalize_result(case, result) == (
        case.get("result")
        if "result" in case
        else case.get("duration_seconds")
        if "duration_seconds" in case
        else case.get("datetime_iso")
        if "datetime_iso" in case
        else case.get("datetime_utc")
        if "datetime_utc" in case
        else case["array_length"]
    )
