import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@jadawel/test/helpers/testApp'
import SidebarAllWorkspaces from '@jadawel/modules/core/components/sidebar/SidebarAllWorkspaces'
import Sidebar from '@jadawel/modules/core/components/sidebar/Sidebar'

const workspace = { id: 1, name: "Aziz's workspace", users: [] }

describe('The name at the top of the sidebar', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, first_name: 'Aziz', preferences: {} })
    await testApp.store.dispatch('workspace/forceCreate', workspace)
    // Whatever else the sidebar loads is not what these tests are about.
    testApp.mock.onAny().reply(200, {})
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const homeHref = () => '/all-workspaces'
  const nameOf = (wrapper) =>
    wrapper.get('.sidebar__workspaces-selector-selected-workspace').text()
  // The menus wrap a `Context`, which knows whether it is open.
  const isOpen = (wrapper, ref) =>
    wrapper.findComponent({ ref }).vm.getRootContext().isOpen()

  test('on the homepage the name opens the menu', async () => {
    const wrapper = await testApp.mount(SidebarAllWorkspaces, {
      props: { workspaces: [workspace], selectedWorkspace: {} },
    })

    expect(nameOf(wrapper)).toBe('Aziz')
    const name = wrapper.get('.sidebar__workspaces-selector-link')
    // A link home would go nowhere: this already is the homepage.
    expect(name.attributes('href')).toBeUndefined()

    expect(isOpen(wrapper, 'userContext')).toBe(false)
    await name.trigger('click')
    await flushPromises()
    expect(isOpen(wrapper, 'userContext')).toBe(true)
  })

  test('on the homepage the arrows open the menu too', async () => {
    const wrapper = await testApp.mount(SidebarAllWorkspaces, {
      props: { workspaces: [workspace], selectedWorkspace: {} },
    })

    await wrapper.get('.sidebar__workspaces-selector-toggle').trigger('click')
    await flushPromises()
    expect(isOpen(wrapper, 'userContext')).toBe(true)
  })

  test('on the homepage the keyboard opens the menu from the name', async () => {
    const wrapper = await testApp.mount(SidebarAllWorkspaces, {
      props: { workspaces: [workspace], selectedWorkspace: {} },
    })

    await wrapper
      .get('.sidebar__workspaces-selector-link')
      .trigger('keydown', { key: 'Enter' })
    await flushPromises()
    expect(isOpen(wrapper, 'userContext')).toBe(true)
  })

  test('inside a workspace it leads home and the arrows open the menu', async () => {
    const wrapper = await testApp.mount(Sidebar, {
      props: {
        workspaces: [workspace],
        selectedWorkspace: workspace,
        applications: [],
      },
    })

    expect(nameOf(wrapper)).toBe("Aziz's workspace")
    expect(
      wrapper.get('.sidebar__workspaces-selector-link').attributes('href')
    ).toBe(homeHref())

    await wrapper.get('.sidebar__workspaces-selector-toggle').trigger('click')
    await flushPromises()
    expect(isOpen(wrapper, 'workspacesContext')).toBe(true)
  })

  test('collapsed, the avatar is all that is left, so it opens the menu', async () => {
    const wrapper = await testApp.mount(SidebarAllWorkspaces, {
      props: {
        workspaces: [workspace],
        selectedWorkspace: {},
        collapsed: true,
      },
    })

    const avatar = wrapper.get('.sidebar__workspaces-selector-link')
    expect(avatar.attributes('href')).toBeUndefined()
    await avatar.trigger('click')
    await flushPromises()
    expect(isOpen(wrapper, 'userContext')).toBe(true)
  })
})
