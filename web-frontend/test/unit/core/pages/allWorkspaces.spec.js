import { TestApp } from '@jadawel/test/helpers/testApp'
import AllWorkspaces from '@jadawel/modules/core/pages/allWorkspaces'
import { CORE_ACTION_SCOPES } from '@jadawel/modules/core/utils/undoRedoConstants'

describe('All workspaces page', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, preferences: {} })
    testApp.mock
      .onGet('/user/dashboard/')
      .reply(200, { workspace_invitations: [] })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('undoes actions of every workspace only while it is shown', async () => {
    testApp.store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      CORE_ACTION_SCOPES.allWorkspaces(false)
    )

    const wrapper = await testApp.mount(AllWorkspaces)
    expect(
      testApp.store.getters['undoRedo/getCurrentScope'].all_workspaces
    ).toBe(true)

    wrapper.unmount()
    expect(
      testApp.store.getters['undoRedo/getCurrentScope'].all_workspaces
    ).toBe(false)
  })

  test('carries Create workspace on its themed bar', async () => {
    const wrapper = await testApp.mount(AllWorkspaces)

    const bar = wrapper.get('.app-header-bar')
    expect(bar.find('.app-header-bar__actions .iconoir-plus').exists()).toBe(
      true
    )
    expect(bar.text()).toContain('allWorkspaces.createWorkspace')
    // Not twice: the content's own header row no longer has it.
    expect(wrapper.get('.all-workspaces__header').text()).not.toContain(
      'allWorkspaces.createWorkspace'
    )
  })
})
