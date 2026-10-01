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
})
