import { TestApp } from '@jadawel/test/helpers/testApp'
import AllWorkspacesWorkspaceBox from '@jadawel/modules/core/components/allWorkspaces/AllWorkspacesWorkspaceBox'

const workspace = { id: 1, name: 'Acme', users: [] }

describe('AllWorkspacesWorkspaceBox', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, preferences: {} })
    await testApp.store.dispatch('workspace/forceCreate', workspace)
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('offers create and members, and leaves settings to the workspace menu', async () => {
    const wrapper = await testApp.mount(AllWorkspacesWorkspaceBox, {
      props: { workspace, applications: [], totalApplicationCount: 0 },
    })

    // Jadawel has no workspace settings pages, so a "Settings" button opened
    // an empty modal. The workspace menu (⋮) shows settings when there are any.
    // Translations resolve to their key in tests.
    expect(
      wrapper
        .findAll('.workspace-box__actions .workspace-box__action')
        .map((button) => button.text())
        .filter(Boolean)
    ).toEqual(['allWorkspaces.create', 'allWorkspaces.members'])
  })
})
