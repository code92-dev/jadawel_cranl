import en from '@jadawel/modules/arabase/locales/en.json'
import ar from '@jadawel/modules/arabase/locales/ar.json'
import {
  ACTION_CATEGORIES,
  STEP_CATALOG,
  TRIGGER_CATEGORIES,
  orderedNodes,
  stepEntry,
  stepSections,
  workflowReadiness,
} from '@jadawel/modules/arabase/automation/stepCatalog'

const fakeType = (type, { trigger = false, name = type } = {}) => ({
  getType: () => type,
  type,
  name,
  description: `${name} step`,
  isTrigger: trigger,
  iconClass: 'iconoir-x',
  image: null,
})

describe('automation step catalogue', () => {
  test('every registered step has a category and a name in both languages', () => {
    const { $registry } = useNuxtApp()
    const keys = $registry.getOrderedList('node').map((type) => type.getType())
    const missing = (lines) => keys.filter((key) => !lines[key])

    expect(keys.length).toBeGreaterThan(10)
    expect(missing(STEP_CATALOG)).toEqual([])
    expect(missing(en.automationSteps.types)).toEqual([])
    expect(missing(ar.automationSteps.types)).toEqual([])
    for (const key of keys) {
      const { isTrigger } = $registry.get('node', key)
      const categories = isTrigger ? TRIGGER_CATEGORIES : ACTION_CATEGORIES
      expect(categories).toContain(STEP_CATALOG[key].category)
    }
  })

  test('an unknown step keeps its own icon and image', () => {
    const entry = stepEntry({ ...fakeType('future'), image: 'future.svg' })

    expect(entry).toMatchObject({
      known: false,
      category: 'logic',
      tone: 'purple',
      icon: 'iconoir-x',
      image: 'future.svg',
    })
    expect(stepEntry(fakeType('smtp_email')).tone).toBe('blue')
  })

  test('sections follow the catalogue order and search every word', () => {
    const types = [
      fakeType('smtp_email', { name: 'Send an email' }),
      fakeType('router', { name: 'Split into branches' }),
      fakeType('local_jadawel_update_row', { name: 'Update a row' }),
      fakeType('local_jadawel_create_row', { name: 'Add a row' }),
    ]

    expect(
      stepSections(types).map((section) => [
        section.category,
        section.nodeTypes.map((type) => type.getType()),
      ])
    ).toEqual([
      ['records', ['local_jadawel_create_row', 'local_jadawel_update_row']],
      ['messages', ['smtp_email']],
      ['logic', ['router']],
    ])
    expect(
      stepSections(types, {
        search: 'BRANCH',
      }).flatMap((section) => section.nodeTypes.map((type) => type.getType()))
    ).toEqual(['router'])
  })

  test('steps are read in order, children and branches included', () => {
    const node = (id, type) => ({ id, type, service: {} })
    const workflow = {
      graph: {
        0: 1,
        1: { next: { '': [2] } },
        2: { children: [4], next: { '': [3] } },
        3: {},
        4: {},
      },
      nodeMap: {
        1: node(1, 'periodic'),
        2: node(2, 'iterator'),
        3: node(3, 'smtp_email'),
        4: node(4, 'local_jadawel_create_row'),
      },
    }

    expect(orderedNodes(workflow).map((n) => n.id)).toEqual([1, 2, 4, 3])
    expect(orderedNodes({})).toEqual([])

    const registry = {
      exists: () => true,
      get: (_, type) => ({
        ...fakeType(type),
        isInError: ({ node: n }) => n.id === 3,
      }),
    }
    const readiness = workflowReadiness(workflow, registry)

    expect(readiness.total).toBe(4)
    expect(readiness.ready).toBe(3)
    expect(readiness.next.node.id).toBe(3)
    expect(readiness.steps.map((step) => step.number)).toEqual([1, 2, 3, 4])
  })
})
