import { KanbanViewType } from '@jadawel/modules/arabase/kanban/viewType'
import kanbanStore from '@jadawel/modules/arabase/kanban/store'

const STACKS = [
  { id: 1, title: 'Open', color: 'blue', count: 2 },
  { id: 2, title: 'Doing', color: 'green', count: 1 },
  { id: null, title: null, color: null, count: 1 },
]

describe('kanban view type', () => {
  const app = { $i18n: { t: (key) => key }, $registry: { get: () => ({}) } }
  const viewType = new KanbanViewType({ app })

  test('registers under the kanban type', () => {
    expect(viewType.getType()).toBe('kanban')
    // The base view type constructor collapses the capability methods into
    // boolean properties.
    expect(viewType.canFilter).toBe(true)
    expect(viewType.canSort).toBe(true)
    expect(viewType.canShare).toBe(false)
  })

  test('resolves its name and description through i18n', () => {
    expect(viewType.getName()).toBe('kanbanViewType.name')
    expect(viewType.getDescription()).toBe('kanbanViewType.description')
  })
})

describe('kanban view type row events', () => {
  const app = { $i18n: { t: (key) => key }, $registry: { get: () => ({}) } }
  const viewType = new KanbanViewType({ app })
  const board = { id: 10, table_id: 5, type: 'kanban', single_select_field: 50 }

  // A store double: the selected view, one stack's loaded rows, and a record
  // of every commit and dispatch the hooks make.
  const contextFor = (selected, stackRows = {}) => {
    const calls = []
    const store = {
      getters: {
        'view/getSelected': selected,
        'page/view/kanban/getStackData': (stackId) => ({
          rows: stackRows[stackId] || [],
          count: (stackRows[stackId] || []).length,
        }),
      },
      commit: (name, payload) => calls.push(['commit', name, payload]),
      dispatch: (name, payload) => {
        calls.push(['dispatch', name, payload])
        return Promise.resolve()
      },
    }
    return { context: { store }, calls }
  }

  test('ignore events unless the selected view is a kanban of the table', async () => {
    const others = [
      null,
      { ...board, table_id: 6 },
      { ...board, type: 'grid' },
      { ...board, single_select_field: null },
    ]
    for (const selected of others) {
      const { context, calls } = contextFor(selected)
      const row = { id: 1, field_50: { id: 1 } }
      viewType.rowCreated(context, 5, [], row, {}, 'page/')
      await viewType.rowUpdated(
        context,
        5,
        [],
        row,
        { ...row, field_50: { id: 2 } },
        {},
        [50],
        'page/'
      )
      viewType.rowDeleted(context, 5, [], row, 'page/')
      if (selected && selected.single_select_field === null) {
        // Without a grouping field only the create refetch happens.
        expect(calls).toEqual([
          ['dispatch', 'page/view/kanban/fetch', { view: selected }],
        ])
      } else {
        expect(calls).toEqual([])
      }
    }
  })

  test('rowCreated refetches the board', () => {
    const { context, calls } = contextFor(board)
    viewType.rowCreated(context, 5, [], { id: 1 }, {}, 'page/')
    expect(calls).toEqual([
      ['dispatch', 'page/view/kanban/fetch', { view: board }],
    ])
  })

  test('rowUpdated refetches both stacks when the row changed stack', async () => {
    const { context, calls } = contextFor(board)
    await viewType.rowUpdated(
      context,
      5,
      [],
      { id: 1, field_50: { id: 1 } },
      { id: 1, field_50: null },
      {},
      [50],
      'page/'
    )
    expect(calls).toEqual([
      ['dispatch', 'page/view/kanban/fetchStack', { view: board, stackId: 1 }],
      [
        'dispatch',
        'page/view/kanban/fetchStack',
        { view: board, stackId: null },
      ],
      ['dispatch', 'page/view/kanban/fetch', { view: board }],
    ])
  })

  test('rowUpdated replaces a loaded row in place when it kept its stack', async () => {
    const other = { id: 2, field_50: { id: 1 } }
    const { context, calls } = contextFor(board, {
      1: [{ id: 1, field_50: { id: 1 }, name: 'old' }, other],
    })
    const updated = { id: 1, field_50: { id: 1 }, name: 'new' }
    await viewType.rowUpdated(
      context,
      5,
      [],
      { id: 1, field_50: { id: 1 }, name: 'old' },
      updated,
      {},
      [],
      'page/'
    )
    expect(calls).toEqual([
      [
        'commit',
        'page/view/kanban/SET_STACK_ROWS',
        { stackId: 1, rows: [updated, other], count: 2, append: false },
      ],
    ])

    // A row that is not loaded in its stack is left alone.
    const unloaded = contextFor(board, { 1: [other] })
    await viewType.rowUpdated(
      unloaded.context,
      5,
      [],
      { id: 1, field_50: { id: 1 } },
      updated,
      {},
      [],
      'page/'
    )
    expect(unloaded.calls).toEqual([])
  })

  test('rowDeleted removes the row from its stack and refetches the board', () => {
    for (const [value, stackId] of [
      [{ id: 3 }, 3],
      [null, null],
      [{}, null],
    ]) {
      const { context, calls } = contextFor(board)
      viewType.rowDeleted(context, 5, [], { id: 7, field_50: value }, 'page/')
      expect(calls).toEqual([
        ['commit', 'page/view/kanban/REMOVE_ROW', { stackId, rowId: 7 }],
        ['dispatch', 'page/view/kanban/fetch', { view: board }],
      ])
    }
  })
})

describe('kanban store', () => {
  const createStore = (client) => {
    const state = kanbanStore.state()
    // Lazy getters: evaluated on access, so they stay fresh after commits —
    // the same contract the real Vuex store gives the actions.
    const getters = {}
    for (const [name, getter] of Object.entries(kanbanStore.getters)) {
      Object.defineProperty(getters, `view/kanban/${name}`, {
        get: () => getter(state),
      })
    }
    // A Vuex-like action context: `this` carries the client the way the real
    // store instance does after `registerModuleNuxtSafe`.
    const self = { $client: client, getters }
    const store = {
      state,
      getters,
      commit: (name, payload) => kanbanStore.mutations[name](state, payload),
    }
    store.getter = (name) => getters[name]
    // Action contexts receive the module-local getters (unprefixed), the
    // way Vuex hands them to a namespaced module.
    const localGetters = {}
    for (const [name, getter] of Object.entries(kanbanStore.getters)) {
      Object.defineProperty(localGetters, name, {
        get: () => getter(state),
      })
    }
    store.dispatch = (name, payload) =>
      kanbanStore.actions[name].call(
        self,
        {
          state,
          getters: localGetters,
          commit: store.commit,
          dispatch: store.dispatch,
        },
        payload
      )
    return store
  }

  // Keys are matched most-specific-first so a board URL never shadows a
  // stack URL (both contain the view id).
  const client = (responses) => ({
    get: (url) => {
      const entry = Object.entries(responses).find(([key]) => url.endsWith(key))
      return Promise.resolve({ data: entry ? entry[1] : {} })
    },
    patch: (url) => Promise.resolve({ data: {} }),
  })

  test('fetch loads the board and the first page of every stack', async () => {
    const store = createStore(
      client({
        [`kanban/10/`]: { stacks: STACKS },
        'stacks/1/': { count: 2, results: [{ id: 11 }, { id: 12 }] },
        'stacks/2/': { count: 1, results: [{ id: 21 }] },
        'stacks/null/': { count: 1, results: [{ id: 31 }] },
      })
    )

    await store.dispatch('fetch', { view: { id: 10 } })

    expect(store.getter('view/kanban/getStacks')).toEqual(STACKS)
    expect(store.getter('view/kanban/getStackData')(1).rows).toHaveLength(2)
    expect(store.getter('view/kanban/getStackData')(null).rows).toEqual([
      { id: 31 },
    ])
    expect(store.getter('view/kanban/getStackData')(1).hasNextPage).toBe(false)
  })

  test('fetchStack appends the next page behind the load-more button', async () => {
    const store = createStore(
      client({
        'stacks/1/': {
          count: 3,
          results: [{ id: 11 }, { id: 12 }, { id: 13 }],
        },
      })
    )
    store.commit('SET_STACKS', STACKS)

    await store.dispatch('fetchStack', { view: { id: 10 }, stackId: 1 })
    const first = store.getter('view/kanban/getStackData')(1)
    expect(first.rows).toHaveLength(3)
    expect(first.hasNextPage).toBe(false)
    expect(first.nextOffset).toBe(3)
  })

  test('moveRow updates the grouping field optimistically and reverts on failure', async () => {
    let failPatch = false
    const store = createStore({
      get: () => Promise.resolve({ data: {} }),
      patch: () =>
        failPatch ? Promise.reject(new Error('nope')) : Promise.resolve({}),
    })
    store.commit('SET_STACKS', STACKS)
    store.commit('SET_STACK_ROWS', {
      stackId: 1,
      rows: [{ id: 11, field_50: { id: 1 } }],
      count: 1,
      append: false,
    })
    store.commit('SET_STACK_ROWS', {
      stackId: 2,
      rows: [],
      count: 0,
      append: false,
    })

    const fields = [{ id: 50, type: 'single_select' }]
    const view = { id: 10, single_select_field: 50 }
    const row = { id: 11, field_50: { id: 1 } }

    await store.dispatch('moveRow', {
      table: { id: 88 },
      view,
      fields,
      row,
      toStackId: 2,
    })

    expect(store.getter('view/kanban/getStackData')(1).rows).toEqual([])
    expect(
      store.getter('view/kanban/getStackData')(2).rows[0].field_50
    ).toEqual({
      id: 2,
    })

    failPatch = true
    await expect(
      store.dispatch('moveRow', {
        table: { id: 88 },
        view,
        fields,
        row: { ...row, field_50: { id: 1 } },
        toStackId: 1,
      })
    ).rejects.toThrow('nope')

    // Reverted: the row is back in stack 2.
    expect(store.getter('view/kanban/getStackData')(2).rows).toHaveLength(1)
    expect(store.getter('view/kanban/getStackData')(1).rows).toEqual([])
  })

  test('moveRow to the null stack clears the grouping value', async () => {
    const store = createStore({
      get: () => Promise.resolve({ data: {} }),
      patch: (url, body) => {
        expect(body.field_50).toBe(null)
        return Promise.resolve({})
      },
    })
    store.commit('SET_STACKS', STACKS)
    store.commit('SET_STACK_ROWS', {
      stackId: 1,
      rows: [{ id: 11, field_50: { id: 1 } }],
      count: 1,
      append: false,
    })

    await store.dispatch('moveRow', {
      table: { id: 88 },
      view: { id: 10, single_select_field: 50 },
      fields: [{ id: 50, type: 'single_select' }],
      row: { id: 11, field_50: { id: 1 } },
      toStackId: null,
    })

    const nullStack = store.getter('view/kanban/getStackData')(null)
    expect(nullStack.rows[0].field_50).toBe(null)
  })
})
