import { PARITY_CASES } from '@jadawel_test_cases/runtime_formula_parity'
import parseJadawelFormula from '@jadawel/modules/core/formula/parser/parser'
import JadawelFormulaExecutionVisitor from '@jadawel/modules/core/formula/parser/formulaExecutionVisitor.js'
import { Timedelta } from '@jadawel/modules/core/utils/duration'
import moment from '@jadawel/modules/core/moment'
import { TestApp } from '@jadawel/test/helpers/testApp'

/**
 * Frontend consumer of the shared cross-runtime formula parity matrix.
 *
 * Every case in `tests/cases/runtime_formula_parity.json` is executed through
 * the real frontend formula stack — parser, runtime registry and execution
 * visitor — exactly as a formula runs in the browser. The same matrix is
 * executed by the backend through its own parser and execution visitor in
 * `backend/tests/jadawel/formula/test_runtime_formula_parity.py`; a case may
 * only be changed together with its backend outcome, never on one side alone.
 *
 * A case succeeds when the visited result equals the declared JSON value
 * (`duration_seconds` / `datetime_iso` / `array_length` normalize Timedelta,
 * Date and exact-boundary range results to JSON-comparable shapes), and fails
 * with category `invalid_argument` when the same expression raises in the
 * other runtime too. One runtime returning null where the other raises is a
 * parity failure and shows up as a failing case here.
 */
describe('cross-runtime formula parity', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  const executeThroughVisitor = (formula, context) => {
    const tree = parseJadawelFormula(formula)
    return new JadawelFormulaExecutionVisitor(
      {
        get(name) {
          return testApp.store.$registry.get('runtimeFormulaFunction', name)
        },
      },
      context
    ).visit(tree)
  }

  const normalizeResult = (caseData, result) => {
    if ('array_length' in caseData) {
      expect(Array.isArray(result)).toBe(true)
      return result.length
    }
    if ('duration_seconds' in caseData) {
      expect(result).toBeInstanceOf(Timedelta)
      return result.ms / 1000
    }
    if ('datetime_iso' in caseData) {
      expect(result).toBeInstanceOf(Date)
      // Wall-clock ISO without timezone, matching the backend's naive
      // datetime.isoformat(timespec='seconds').
      return moment(result).format('YYYY-MM-DDTHH:mm:ss')
    }
    if ('datetime_utc' in caseData) {
      expect(result).toBeInstanceOf(Date)
      // Offset-bearing inputs are compared as UTC instants, so the two
      // runtimes agree regardless of the test machine's timezone.
      return moment.utc(result).format('YYYY-MM-DDTHH:mm:ss[Z]')
    }
    return result
  }

  test.each(PARITY_CASES)('parity case %s', ({ formula, context = {} }) => {
    const caseData = PARITY_CASES.find((c) => c.formula === formula)

    if ('error' in caseData) {
      expect(() => executeThroughVisitor(formula, context)).toThrow()
      return
    }

    const result = executeThroughVisitor(formula, context)
    const normalized = normalizeResult(caseData, result)
    const expected =
      'result' in caseData
        ? caseData.result
        : 'duration_seconds' in caseData
          ? caseData.duration_seconds
          : 'datetime_iso' in caseData
            ? caseData.datetime_iso
            : 'datetime_utc' in caseData
              ? caseData.datetime_utc
              : caseData.array_length
    expect(normalized).toEqual(expected)
  })
})
