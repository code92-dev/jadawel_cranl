import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@jadawel/test/helpers/testApp'
import WorkspaceMemberInviteModal from '@jadawel/modules/core/components/workspace/WorkspaceMemberInviteModal'

describe('WorkspaceMemberInviteModal with a workspace to choose', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, preferences: {} })
    for (const workspace of [
      { id: 1, name: 'Acme', permissions: 'ADMIN', users: [] },
      { id: 2, name: 'Widelab', permissions: 'MEMBER', users: [] },
      { id: 3, name: 'Zeta', permissions: 'ADMIN', users: [] },
    ]) {
      await testApp.store.dispatch('workspace/forceCreate', workspace)
    }
    testApp.mock.onGet(/\/workspaces\/\d+\/permissions\//).reply(200, [])
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  async function open(preselected = null) {
    const workspaces = testApp.store.getters['workspace/getAllSorted']
    const wrapper = await testApp.mount(WorkspaceMemberInviteModal, {
      props: {
        workspace: preselected
          ? workspaces.find((workspace) => workspace.id === preselected)
          : null,
        workspaces,
      },
    })
    await wrapper.vm.show()
    await flushPromises()
    return wrapper
  }

  test('offers the workspaces where the user is an admin', async () => {
    const wrapper = await open()

    // Inviting is admin only, so only those workspaces' permissions load.
    expect(
      testApp.mock.history.get.map((request) => request.url).sort()
    ).toEqual(['/workspaces/1/permissions/', '/workspaces/3/permissions/'])
    expect(wrapper.vm.invitableWorkspaces.map(({ name }) => name)).toEqual([
      'Acme',
      'Zeta',
    ])
    // Without a workspace to start from, the first one is chosen.
    expect(wrapper.vm.targetWorkspace.name).toBe('Acme')
  })

  test('starts from the given workspace and invites to the chosen one', async () => {
    testApp.mock
      .onPost('/workspaces/invitations/workspace/3/')
      .reply(200, { id: 9, email: 'sara@example.com' })
    const wrapper = await open(3)

    expect(wrapper.vm.targetWorkspace.name).toBe('Zeta')
    await wrapper.vm.inviteSubmitted({
      email: 'sara@example.com',
      permissions: 'MEMBER',
    })

    expect(testApp.mock.history.post).toHaveLength(1)
    expect(wrapper.emitted('invite-submitted')[0][0].id).toBe(3)
  })
})
