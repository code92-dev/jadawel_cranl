import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { TestApp } from '@jadawel/test/helpers/testApp'
import KanbanView from '@jadawel/modules/arabase/kanban/components/KanbanView'

/**
 * The board component against the real kanban store: what it renders from the
 * board and stack responses, and how often it asks for them. The board is
 * loaded once per view — on mount and again only when the view changes.
 */
const fieldData = [
  { id: 1, name: 'Name', type: 'text', primary: true, text_default: '' },
  {
    id: 2,
    name: 'Status',
    type: 'single_select',
    primary: false,
    select_options: [
      { id: 1, value: 'Open', color: 'blue' },
      { id: 2, value: 'Doing', color: 'green' },
    ],
  },
]

const STACKS = [
  { id: 1, title: 'Open', color: 'blue', count: 2 },
  { id: 2, title: 'Doing', color: 'green', count: 1 },
  { id: null, title: null, color: null, count: 0 },
]

const STACK_ROWS = {
  1: [
    { id: 11, order: '1', field_1: 'Alpha', field_2: { id: 1 } },
    { id: 12, order: '2', field_1: 'Beta', field_2: { id: 1 } },
  ],
  2: [{ id: 21, order: '3', field_1: 'Gamma', field_2: { id: 2 } }],
  null: [],
}

const FIELD_OPTIONS = {
  1: { hidden: false, order: 0 },
  2: { hidden: true, order: 1 },
}

describe('KanbanView', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(async () => {
    await testApp.afterEach()
    vi.restoreAllMocks()
  })

  const mockBoard = (viewId) => {
    testApp.mock
      .onGet(`/database/views/kanban/${viewId}/`)
      .reply(200, { stacks: STACKS, field_options: FIELD_OPTIONS })
    for (const [stackId, rows] of Object.entries(STACK_ROWS)) {
      testApp.mock
        .onGet(`/database/views/kanban/${viewId}/stacks/${stackId}/`)
        .reply(200, { count: rows.length, results: rows })
    }
  }

  const boardRequests = (viewId) =>
    testApp.mock.history.get.filter(
      (request) => request.url === `/database/views/kanban/${viewId}/`
    )

  const stackRequests = (viewId) =>
    testApp.mock.history.get.filter((request) =>
      request.url.startsWith(`/database/views/kanban/${viewId}/stacks/`)
    )

  const fetchDispatches = (dispatch) =>
    dispatch.mock.calls.filter(([name]) => name === 'page/view/kanban/fetch')

  const kanbanView = (id, table) => ({
    id,
    table_id: table.id,
    name: `Board ${id}`,
    type: 'kanban',
    single_select_field: 2,
    decorations: [],
  })

  const mountBoard = async () => {
    const table = testApp.mockServer.createTable()
    const { application } =
      await testApp.mockServer.createAppAndWorkspace(table)
    testApp.mockServer.createFields(application, table, fieldData)
    await store.dispatch('field/fetchAll', { table })
    const fields = store.getters['field/getAll']
    mockBoard(10)

    const dispatch = vi.spyOn(store, 'dispatch')
    const wrapper = await testApp.mount(KanbanView, {
      props: {
        database: application,
        table,
        view: kanbanView(10, table),
        fields,
        readOnly: false,
        storePrefix: 'page/',
      },
    })
    await flushPromises()
    return { wrapper, dispatch, table }
  }

  test('renders one stack per option with its title, count and cards', async () => {
    const { wrapper } = await mountBoard()

    const stacks = wrapper.findAll('.kanban-view__stack')
    expect(stacks).toHaveLength(3)
    expect(
      stacks.map((stack) => stack.find('.kanban-view__stack-title').text())
    ).toEqual(['Open', 'Doing', 'kanbanView.emptyStack'])
    expect(
      stacks.map((stack) => stack.find('.kanban-view__stack-count').text())
    ).toEqual(['2', '1', '0'])
    expect(
      stacks.map((stack) => stack.findAll('.kanban-view__stack-badge').length)
    ).toEqual([1, 1, 0])
    expect(stacks[0].find('.kanban-view__stack-badge').classes()).toContain(
      'background-color--blue'
    )

    const cardTexts = stacks.map((stack) =>
      stack.findAll('.kanban-view__card').map((card) => card.text())
    )
    expect(cardTexts).toHaveLength(3)
    expect(cardTexts[0]).toHaveLength(2)
    expect(cardTexts[0][0]).toContain('Alpha')
    expect(cardTexts[0][1]).toContain('Beta')
    expect(cardTexts[1]).toHaveLength(1)
    expect(cardTexts[1][0]).toContain('Gamma')
    expect(cardTexts[2]).toEqual([])
    // The board's field options hide the grouping field on the cards.
    expect(cardTexts[0][0]).toContain('Name')
    expect(cardTexts[0][0]).not.toContain('Status')
    expect(wrapper.findAll('.kanban-view__more')).toHaveLength(0)
  })

  test('fetches the board once on mount', async () => {
    const { dispatch } = await mountBoard()

    expect(fetchDispatches(dispatch)).toHaveLength(1)
    expect(fetchDispatches(dispatch)[0][1].view.id).toBe(10)
    expect(boardRequests(10)).toHaveLength(1)
    expect(stackRequests(10)).toHaveLength(STACKS.length)
  })

  test('fetches the board once more when the view changes', async () => {
    const { wrapper, dispatch, table } = await mountBoard()
    mockBoard(20)

    await wrapper.setProps({ view: kanbanView(20, table) })
    await flushPromises()

    expect(fetchDispatches(dispatch)).toHaveLength(2)
    expect(fetchDispatches(dispatch)[1][1].view.id).toBe(20)
    expect(boardRequests(10)).toHaveLength(1)
    expect(boardRequests(20)).toHaveLength(1)
    expect(stackRequests(20)).toHaveLength(STACKS.length)
  })

  test('does not refetch when the same view object is updated in place', async () => {
    const { wrapper, dispatch, table } = await mountBoard()

    await wrapper.setProps({
      view: { ...kanbanView(10, table), name: 'Renamed' },
    })
    await flushPromises()

    expect(fetchDispatches(dispatch)).toHaveLength(1)
    expect(boardRequests(10)).toHaveLength(1)
  })
})
