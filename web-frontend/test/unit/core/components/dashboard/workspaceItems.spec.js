import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@jadawel/test/helpers/testApp'
import WorkspaceItems from '@jadawel/modules/core/components/dashboard/WorkspaceItems'

const workspace = { id: 1, name: 'Acme', users: [] }

describe('WorkspaceItems', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, preferences: {} })
    // The preference endpoint echoes what was stored, like the backend does.
    testApp.mock
      .onPatch('/user/preferences/')
      .reply((config) => [200, JSON.parse(config.data)])
    await testApp.store.dispatch('workspace/forceCreate', workspace)
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  async function createApplication(fields) {
    await testApp.store.dispatch('application/forceCreate', {
      workspace,
      // Each application type populates its own children.
      tables: [],
      pages: [],
      workflows: [],
      last_viewed: null,
      ...fields,
    })
    return testApp.store.getters['application/get'](fields.id)
  }

  async function mount(applications) {
    return await testApp.mount(WorkspaceItems, {
      props: { workspace, applications },
    })
  }

  test('lists every item by its own name and type, most recently viewed first', async () => {
    const applications = [
      await createApplication({
        id: 1,
        name: 'CRM',
        type: 'database',
        order: 1,
        last_viewed: '2026-01-01T10:00:00Z',
      }),
      await createApplication({
        id: 2,
        name: 'Sales',
        type: 'dashboard',
        order: 2,
        last_viewed: '2026-01-02T10:00:00Z',
      }),
      await createApplication({ id: 3, name: 'Website', type: 'builder' }),
    ]
    const wrapper = await mount(applications)

    expect(wrapper.find('.dashboard__section-count').text()).toBe('3')
    const cards = wrapper.findAll('.item-card')
    expect(cards.map((card) => card.find('.item-card__name').text())).toEqual([
      'Sales',
      'CRM',
      'Website',
    ])
    // Translations resolve to their key in tests.
    expect(cards[1].find('.item-card__meta').text()).toContain(
      'applicationType.database'
    )
    expect(cards[2].find('.item-card__meta').text()).toContain(
      'common.neverViewed'
    )
  })

  test('sorts the way the homepage does and remembers it', async () => {
    testApp.authenticate({
      id: 1,
      preferences: { all_workspaces_sort_by: 'name_asc' },
    })
    const applications = [
      await createApplication({ id: 1, name: 'Website', type: 'builder' }),
      await createApplication({ id: 2, name: 'CRM', type: 'database' }),
    ]
    const wrapper = await mount(applications)

    expect(
      wrapper.findAll('.item-card__name').map((name) => name.text())
    ).toEqual(['CRM', 'Website'])
  })

  test('filters by type and says when nothing matches', async () => {
    const applications = [
      await createApplication({ id: 1, name: 'CRM', type: 'database' }),
      await createApplication({ id: 2, name: 'Website', type: 'builder' }),
    ]
    const wrapper = await mount(applications)

    wrapper.vm.$.setupState.selectedTypes = ['builder']
    await flushPromises()
    expect(
      wrapper.findAll('.item-card__name').map((name) => name.text())
    ).toEqual(['Website'])

    wrapper.vm.$.setupState.selectedTypes = ['dashboard']
    await flushPromises()
    expect(wrapper.findAll('.item-card')).toHaveLength(0)
    expect(wrapper.find('.workspace-items__no-match').text()).toBe(
      'allWorkspaces.noFilterMatches'
    )
  })
})
