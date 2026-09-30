import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@jadawel/test/helpers/testApp'
import { ArabasePlugin } from '@jadawel/modules/arabase/plugins'
import ShareDashboardLink from '@jadawel/modules/arabase/dashboard/components/ShareDashboardLink'
import AddToMyDashboards from '@jadawel/modules/arabase/savedDashboards/components/AddToMyDashboards'
import MyDashboardsMenuItem from '@jadawel/modules/arabase/savedDashboards/components/MyDashboardsMenuItem'
import SavedDashboardCard from '@jadawel/modules/arabase/savedDashboards/components/SavedDashboardCard'
import AddSavedDashboardModal from '@jadawel/modules/arabase/savedDashboards/components/AddSavedDashboardModal'
import SidebarUserContext from '@jadawel/modules/core/components/sidebar/SidebarUserContext'

/**
 * "My dashboards" (لوحاتي) — docs/MY_DASHBOARDS.md: where it is reached from,
 * how a card stands for its dashboard, and how the add dialog asks for a
 * protected link's password.
 */
const card = (overrides = {}) => ({
  id: 4,
  source: 'workspace',
  title: 'Sales',
  preview: [
    { type: 'summary', width: 3, height: 2 },
    { type: 'chart', width: 9, height: 4 },
  ],
  status: 'ok',
  source_name: 'Finance',
  dashboard_id: 12,
  ...overrides,
})

describe('where My dashboards is reached from', () => {
  const pluginFor = ({ member, canShare }) =>
    new ArabasePlugin({
      app: {
        $store: { getters: { 'workspace/get': () => (member ? {} : null) } },
        $hasPermission: () => canShare,
      },
    })
  const dashboard = { id: 12, workspace: { id: 3 } }

  test('the user menu gets the entry above My settings', () => {
    expect(
      pluginFor({ member: true }).getUserContextComponentsBeforeSettings()
    ).toEqual([MyDashboardsMenuItem])
  })

  test('any member can pin a dashboard; only an editor can share it', () => {
    expect(
      pluginFor({
        member: true,
        canShare: true,
      }).getAdditionalDashboardHeaderComponents(dashboard)
    ).toEqual([AddToMyDashboards, ShareDashboardLink])
    expect(
      pluginFor({
        member: true,
        canShare: false,
      }).getAdditionalDashboardHeaderComponents(dashboard)
    ).toEqual([AddToMyDashboards])
    // A template preview is no workspace of the user's.
    expect(
      pluginFor({
        member: false,
        canShare: false,
      }).getAdditionalDashboardHeaderComponents(dashboard)
    ).toEqual([])
  })

  test('the entry sits directly above My settings', async () => {
    const testApp = new TestApp()
    const workspace = { id: 1, name: 'Finance', users: [] }
    testApp.store.commit('workspace/SET_ITEMS', [workspace])
    testApp.mock.onGet('/auth-provider/login-options/').reply(200, {})
    const wrapper = await testApp.mount(SidebarUserContext, {
      props: { workspaces: [workspace], selectedWorkspace: workspace },
    })
    // The menu renders its items once it is opened.
    await wrapper.vm.show(document.body, 'bottom', 'left')
    await flushPromises()

    const labels = wrapper
      .findAll('.sidebar__user .context__menu-item')
      .map((item) => item.text())
    const settings = labels.indexOf('sidebar.settings')
    expect(settings).toBeGreaterThan(0)
    expect(labels[settings - 1]).toBe('myDashboards.title')
    await testApp.afterEach()
  })
})

describe('SavedDashboardCard', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountCard = (overrides) =>
    testApp.mount(SavedDashboardCard, { props: { card: card(overrides) } })

  test('sketches the dashboard on its 12-column board', async () => {
    const wrapper = await mountCard()

    const blocks = wrapper.findAll('.saved-dashboard-card__block')
    expect(blocks.map((block) => block.attributes('style'))).toEqual([
      'grid-column: span 3; grid-row: span 2;',
      'grid-column: span 9; grid-row: span 4;',
    ])
    expect(blocks[0].classes()).toContain('saved-dashboard-card__block--number')
    expect(blocks[1].classes()).toContain('saved-dashboard-card__block--chart')
    expect(wrapper.find('.saved-dashboard-card__title').text()).toBe('Sales')
    expect(wrapper.find('.saved-dashboard-card__source').text()).toBe('Finance')
    expect(wrapper.find('.saved-dashboard-card__status').exists()).toBe(false)
  })

  test('opens when it can, and asks for the password when it changed', async () => {
    const open = await mountCard()
    await open.find('.saved-dashboard-card__preview').trigger('click')
    expect(open.emitted('open')).toHaveLength(1)

    const locked = await mountCard({ source: 'link', status: 'password' })
    await locked.find('.saved-dashboard-card__preview').trigger('click')
    expect(locked.emitted('open')).toBeUndefined()
    expect(locked.emitted('password')).toHaveLength(1)
    expect(locked.find('.saved-dashboard-card__status').text()).toBe(
      'myDashboards.status.password'
    )
    // A link on this server does not name the owner's workspace.
    expect(locked.find('.saved-dashboard-card__source').text()).toBe(
      'myDashboards.sharedLink'
    )

    const gone = await mountCard({ status: 'unavailable' })
    await gone.find('.saved-dashboard-card__preview').trigger('click')
    expect(gone.emitted('open')).toBeUndefined()
    expect(gone.classes()).toContain('saved-dashboard-card--blocked')
  })
})

describe('AddSavedDashboardModal', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountModal = async (available = []) => {
    testApp.mock
      .onGet('/arabase/my-dashboards/available/')
      .reply(200, available)
    const wrapper = await testApp.mount(AddSavedDashboardModal)
    wrapper.vm.show()
    await flushPromises()
    return wrapper
  }

  test('adds a dashboard from one of the users workspaces', async () => {
    const wrapper = await mountModal([
      {
        id: 3,
        name: 'Finance',
        dashboards: [
          { id: 12, name: 'Sales', saved: false },
          { id: 13, name: 'Costs', saved: true },
        ],
      },
    ])
    testApp.mock
      .onPost('/arabase/my-dashboards/workspace/', { dashboard_id: 12 })
      .reply(200, card())

    const items = wrapper.findAll('.add-saved-dashboard__item')
    expect(items).toHaveLength(2)
    expect(items[1].find('.add-saved-dashboard__added').exists()).toBe(true)

    await items[0].find('button').trigger('click')
    await flushPromises()

    expect(wrapper.emitted('added')).toEqual([[card()]])
    expect(
      wrapper
        .findAll('.add-saved-dashboard__item')[0]
        .find('.add-saved-dashboard__added')
        .exists()
    ).toBe(true)
  })

  test('a protected link asks for its password before it is added', async () => {
    const wrapper = await mountModal()
    const url = 'https://other.example/public/dashboard/abc'
    testApp.mock
      .onPost('/arabase/my-dashboards/link/', { url, password: '' })
      .reply(401, {
        error: 'ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED',
        detail: 'The dashboard is password protected.',
      })
    testApp.mock
      .onPost('/arabase/my-dashboards/link/', { url, password: 'secret-123' })
      .reply(200, card({ source: 'remote', source_name: 'other.example' }))

    await wrapper.findAll('.segment-control__button')[1].trigger('click')
    await wrapper.find('input').setValue(url)
    expect(wrapper.find('input[type="password"]').exists()).toBe(false)

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('added')).toBeUndefined()
    const password = wrapper.find('input[type="password"]')
    expect(password.exists()).toBe(true)

    await password.setValue('secret-123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.emitted('added')[0][0].source).toBe('remote')
  })

  test('explains a link that is not a dashboard link', async () => {
    const wrapper = await mountModal()
    testApp.mock.onPost('/arabase/my-dashboards/link/').reply(400, {
      error: 'ERROR_SAVED_DASHBOARD_LINK_INVALID',
      detail: 'That is not the public link of a dashboard.',
    })

    await wrapper.findAll('.segment-control__button')[1].trigger('click')
    await wrapper.find('input').setValue('https://example.com/nope')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain(
      'myDashboards.errors.ERROR_SAVED_DASHBOARD_LINK_INVALID.title'
    )
    expect(wrapper.emitted('added')).toBeUndefined()
  })
})
