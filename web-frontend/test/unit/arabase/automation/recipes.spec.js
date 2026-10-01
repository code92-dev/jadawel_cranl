import en from '@jadawel/modules/arabase/locales/en.json'
import ar from '@jadawel/modules/arabase/locales/ar.json'
import {
  RECIPES,
  availableRecipes,
  buildRecipe,
  recipeLabelKeys,
  recipeSections,
  recipeTypes,
  scheduleValues,
} from '@jadawel/modules/arabase/automation/recipes'

const lookup = (messages, key) =>
  key.split('.').reduce((value, part) => value?.[part], messages)

describe('automation recipes', () => {
  // Every recipe is offered on an instance configured for every trigger; the
  // email trigger is the one that depends on configuration (inbound email).
  let settings
  beforeEach(() => {
    const { $store } = useNuxtApp()
    settings = $store.getters['settings/get']
    $store.commit('settings/SET_SETTINGS', {
      ...settings,
      inbound_email_enabled: true,
    })
  })
  afterEach(() => {
    useNuxtApp().$store.commit('settings/SET_SETTINGS', settings)
  })

  test('every recipe starts with a trigger, continues with actions and is named', () => {
    const { $registry } = useNuxtApp()

    expect(availableRecipes($registry)).toHaveLength(RECIPES.length)
    for (const recipe of RECIPES) {
      const [trigger, ...steps] = recipeTypes(recipe)
      expect($registry.get('node', trigger).isTrigger).toBe(true)
      for (const step of steps) {
        expect($registry.get('node', step).isWorkflowAction).toBe(true)
      }
      expect(recipeLabelKeys(recipe)).toHaveLength(steps.length + 1)
      for (const messages of [en, ar]) {
        const text = messages.automationRecipes.recipes[recipe.key]
        expect(text.name).toBeTruthy()
        expect(text.description).toBeTruthy()
        for (const key of recipeLabelKeys(recipe)) {
          expect(lookup(messages, key)).toBeTruthy()
        }
      }
    }
  })

  test('every event and every step is used by at least one recipe', () => {
    const { $registry } = useNuxtApp()
    const used = new Set(availableRecipes($registry).flatMap(recipeTypes))
    const unused = $registry
      .getOrderedList('node')
      .map((type) => type.getType())
      .filter((type) => !used.has(type))

    expect(unused).toEqual([])
    expect(used).toContain('slack_write_message')
  })

  test('recipes are grouped, every group named in both languages', () => {
    const { $registry } = useNuxtApp()
    const sections = recipeSections($registry)

    expect(sections.map((section) => section.category)).toEqual([
      'notify',
      'records',
      'schedule',
      'connect',
    ])
    expect(sections.flatMap((section) => section.recipes)).toHaveLength(
      RECIPES.length
    )
    for (const { category } of sections) {
      expect(en.automationRecipes.categories[category]).toBeTruthy()
      expect(ar.automationRecipes.categories[category]).toBeTruthy()
    }
  })

  test("a loop's steps are built inside it, and the next step after it", async () => {
    const recipe = {
      key: 'loop',
      trigger: 'periodic',
      steps: [
        {
          type: 'iterator',
          children: ['smtp_email', 'local_jadawel_create_row'],
        },
        'local_jadawel_update_row',
      ],
    }
    const created = []
    const store = {
      dispatch: vi.fn(async (action, payload) => {
        if (action === 'automationWorkflowNode/create') {
          const node = { id: created.length + 1, type: payload.type }
          created.push({ ...payload, node })
          return node
        }
      }),
      getters: { 'automationWorkflowNode/findById': () => null },
    }

    await buildRecipe({
      store,
      client: { patch: vi.fn().mockResolvedValue({}) },
      workflow: { id: 1 },
      recipe,
      labels: [],
    })

    const placement = created.map(({ type, referenceNode, position }) => [
      type,
      referenceNode?.type || null,
      position || null,
    ])
    expect(placement).toEqual([
      ['periodic', null, null],
      ['iterator', 'periodic', 'south'],
      ['smtp_email', 'iterator', 'child'],
      ['local_jadawel_create_row', 'smtp_email', 'south'],
      ['local_jadawel_update_row', 'iterator', 'south'],
    ])
  })

  test('a recipe whose step is not installed is not offered', () => {
    const registry = { exists: (_, type) => type !== 'ai_agent' }

    expect(
      availableRecipes(registry).map((recipe) => recipe.key)
    ).not.toContain('ai_fill_row')
  })

  test('building a recipe creates each step after the last and names them', async () => {
    const recipe = RECIPES.find((r) => r.key === 'daily_digest')
    const workflow = { id: 5 }
    const created = []
    const store = {
      dispatch: vi.fn(async (action, payload) => {
        if (action === 'automationWorkflowNode/create') {
          const node = { id: created.length + 10, type: payload.type }
          created.push({ ...payload, node })
          return node
        }
      }),
      getters: {
        'automationWorkflowNode/findById': (_, id) => ({ id }),
      },
    }
    const patch = vi.fn().mockResolvedValue({})
    const client = { patch }

    const nodes = await buildRecipe({
      store,
      client,
      workflow,
      recipe,
      labels: ['Every morning', 'Find the rows', 'Email the digest'],
    })

    expect(nodes.map((node) => node.type)).toEqual([
      'periodic',
      'local_jadawel_list_rows',
      'smtp_email',
    ])
    expect(created[0].referenceNode).toBeNull()
    expect(created[1]).toMatchObject({
      referenceNode: { id: 10 },
      position: 'south',
      output: '',
    })
    expect(created[2].referenceNode).toEqual({ id: 11, type: recipe.steps[0] })
    expect(patch).toHaveBeenCalledWith('automation/node/12/', {
      label: 'Email the digest',
    })
    // "Daily digest" is set to run daily at 08:00, as its name says.
    expect(patch).toHaveBeenCalledWith('automation/node/10/', {
      label: 'Every morning',
      service: scheduleValues({ interval: 'DAY', hour: 8, minute: 0 }),
    })
    expect(patch).toHaveBeenCalledTimes(3)
  })

  test("a schedule is stored in UTC for the builder's local time", () => {
    const now = new Date(2026, 8, 28, 12, 0)
    const values = scheduleValues(
      { interval: 'WEEK', day_of_week: 6, hour: 8, minute: 30 },
      now
    )
    const local = new Date(now)
    local.setDate(local.getDate() + 6 - ((local.getDay() + 6) % 7))
    local.setHours(8, 30, 0, 0)

    expect(values).toEqual({
      interval: 'WEEK',
      hour: local.getUTCHours(),
      minute: local.getUTCMinutes(),
      day_of_week: (local.getUTCDay() + 6) % 7,
    })
    // Sunday 08:30 local time, read back.
    expect([local.getDay(), local.getHours(), local.getMinutes()]).toEqual([
      0, 8, 30,
    ])
  })

  test('the email recipe is only offered once inbound email is configured', () => {
    const { $registry, $store } = useNuxtApp()
    const offered = () =>
      availableRecipes($registry).map((recipe) => recipe.key)

    expect(offered()).toContain('email_to_row')

    $store.commit('settings/SET_SETTINGS', {
      ...settings,
      inbound_email_enabled: false,
    })
    expect(offered()).not.toContain('email_to_row')
  })
})
