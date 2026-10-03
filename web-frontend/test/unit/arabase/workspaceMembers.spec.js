import { TestApp } from '@jadawel/test/helpers/testApp'
import WorkspaceMembers from '@jadawel/modules/arabase/pages/workspaceMembers'

const user = (id, name, email, permissions) => ({
  id: id * 10,
  user_id: id,
  name,
  email,
  permissions,
})

describe('The members of every workspace', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    testApp.authenticate({ id: 1, first_name: 'Aziz', preferences: {} })
    await testApp.store.dispatch('workspace/forceCreate', {
      id: 1,
      name: 'Acme',
      order: 1,
      permissions: 'ADMIN',
      users: [
        user(2, 'Sara', 'sara@example.com', 'MEMBER'),
        user(1, 'Aziz', 'aziz@example.com', 'ADMIN'),
        user(3, 'Badr', 'badr@example.com', 'MEMBER'),
      ],
    })
    await testApp.store.dispatch('workspace/forceCreate', {
      id: 2,
      name: 'Widelab',
      order: 2,
      permissions: 'MEMBER',
      users: [
        user(1, 'Aziz', 'aziz@example.com', 'MEMBER'),
        user(4, 'Huda', 'huda@example.com', 'ADMIN'),
      ],
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('lists each workspace with its members, the user first', async () => {
    const wrapper = await testApp.mount(WorkspaceMembers, {
      global: { stubs: { AppUtilities: true } },
    })

    const boxes = wrapper.findAll('.workspace-members__box')
    expect(boxes.map((box) => box.get('.workspace-box__name').text())).toEqual([
      'Acme',
      'Widelab',
    ])

    const names = boxes[0]
      .findAll('.workspace-members__member-name')
      .map((name) => name.text())
    // Translations resolve to their key in tests.
    expect(names).toEqual(['Aziz workspaceMembers.you', 'Badr', 'Sara'])
    expect(boxes[0].findAll('.workspace-members__member-email')[2].text()).toBe(
      'sara@example.com'
    )
    expect(boxes[0].findAll('.workspace-box__action')).toHaveLength(2)
  })

  test('keeps the names hidden where the user is not an admin', async () => {
    const wrapper = await testApp.mount(WorkspaceMembers, {
      global: { stubs: { AppUtilities: true } },
    })

    const widelab = wrapper.findAll('.workspace-members__box')[1]
    expect(widelab.find('.workspace-members__list').exists()).toBe(false)
    expect(widelab.find('.workspace-members__hidden').text()).toBe(
      'workspaceMembers.adminsOnly'
    )
    // The count is still shown, as on the workspaces homepage.
    expect(widelab.get('.workspace-box__meta-text').text()).toContain(
      'allWorkspaces.membersCount'
    )
    expect(widelab.find('.workspace-box__actions').exists()).toBe(false)
  })
})
