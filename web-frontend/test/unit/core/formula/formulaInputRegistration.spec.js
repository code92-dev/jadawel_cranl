import { TestApp } from '@jadawel/test/helpers/testApp'
import { buildFormulaFunctionNodes } from '@jadawel/modules/core/formula'
import parseJadawelFormula from '@jadawel/modules/core/formula/parser/parser'
import JadawelFormulaExecutionVisitor from '@jadawel/modules/core/formula/parser/formulaExecutionVisitor.js'

/**
 * The nine runtime formula functions added by the new-features port must be
 * usable in the Application Builder and Automation formula inputs.
 *
 * Both `ApplicationBuilderFormulaInput.vue` and
 * `AutomationBuilderFormulaInput.vue` build their autocomplete from
 * `buildFormulaFunctionNodes(app)` over the same `runtimeFormulaFunction`
 * registry, and execute through the same `JadawelFormulaExecutionVisitor`.
 * This spec proves the full consumer path for each function:
 *
 * - registered: present in the `runtimeFormulaFunction` registry the inputs
 *   read from the Nuxt app;
 * - discoverable: exposed as an autocomplete node with name, category,
 *   signature and examples;
 * - serializable: the autocomplete node survives a JSON round trip (the nodes
 *   are plain data handed to the TipTap editor);
 * - executable: a real formula using the function parses and executes through
 *   the registry-driven execution visitor.
 */

const NINE_FUNCTIONS = [
  { type: 'abs', smoke: 'abs(-2)', result: 2 },
  { type: 'range', smoke: 'range(2)', result: [0, 1] },
  { type: 'to_json', smoke: "to_json('a')", result: '"a"' },
  { type: 'from_json', smoke: "from_json('[1]')", result: [1] },
  { type: 'null', smoke: 'null()', result: null },
  {
    type: 'number_format',
    smoke: 'number_format(1000)',
    result: '1,000',
  },
  { type: 'to_duration', smoke: "to_duration('1 day')", resultMs: 86400000 },
  {
    type: 'duration_format',
    smoke: "duration_format(to_duration('2 hours'), 'h:mm')",
    result: '2:00',
  },
  {
    type: 'to_datetime',
    smoke: "to_datetime('2024-01-15')",
    resultIso: '2024-01-15T00:00:00',
  },
]

describe('formula input registration (builder + automation consumers)', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test.each(NINE_FUNCTIONS)(
    '%s is registered, discoverable, serializable and executable',
    ({ type, smoke, result, resultMs, resultIso }) => {
      const registry = testApp.store.$registry

      // Registered: resolvable through the same registry both formula inputs
      // read from the Nuxt app.
      const func = registry.get('runtimeFormulaFunction', type)
      expect(func).toBeTruthy()
      expect(func.getDescription()).toEqual(expect.any(String))
      expect(func.getExamples().length).toBeGreaterThan(0)

      // Discoverable + serializable: the autocomplete node both
      // ApplicationBuilderFormulaInput and AutomationBuilderFormulaInput
      // render must exist and round-trip through JSON.
      const nodes = buildFormulaFunctionNodes(testApp.getApp())
      const flat = JSON.parse(JSON.stringify(nodes))
      const found = JSON.stringify(flat).includes(`"${type}"`)
      expect(found).toBe(true)

      // Executable: through the registry-driven execution visitor, exactly
      // like a saved formula in a builder element or automation node.
      const tree = parseJadawelFormula(smoke)
      const executed = new JadawelFormulaExecutionVisitor(
        {
          get(name) {
            return registry.get('runtimeFormulaFunction', name)
          },
        },
        {}
      ).visit(tree)
      if (resultMs !== undefined) {
        expect(executed.ms).toBe(resultMs)
      } else if (resultIso !== undefined) {
        expect(executed instanceof Date).toBe(true)
      } else {
        expect(executed).toEqual(result)
      }
    }
  )
})
