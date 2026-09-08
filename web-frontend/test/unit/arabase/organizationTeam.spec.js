import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@jadawel/test/helpers/testApp'
import OrganizationDetail from '../../../../plugins/jadawel_organizations/web-frontend/modules/jadawel-organizations/pages/organization.vue'

describe('Organization Team administration', () => {
  let app

  beforeEach(() => {
    app = new TestApp()
  })

  afterEach(async () => {
    await app.afterEach()
  })

  test('shows access state and adds an existing user', async () => {
    app.mock.onGet('/organizations/org-1/').reply(200, {
      id: 'org-1',
      name: 'Acme',
      status: 'active',
      provisioning_status: 'ready',
      members: [
        { id: 1, email: 'owner@example.com', role: 'owner', suspended: false },
      ],
      workspaces: [],
      effective_entitlement: { source: 'manual', seat_limit: 5 },
    })
    app.mock.onGet('/organizations/org-1/invitations/').reply(200, [])
    app.mock.onPost('/organizations/org-1/members/').reply(201, {
      id: 2,
      email: 'member@example.com',
      role: 'member',
      suspended: false,
    })

    const wrapper = await app.mount(OrganizationDetail, {
      props: { routeOrganizationId: 'org-1' },
    })
    expect(wrapper.text()).toContain('Acme')
    expect(wrapper.text()).toContain('manual')

    const addForm = wrapper.find('[data-testid="member-add-form"]')
    await addForm.find('input[type="number"]').setValue('2')
    await addForm.trigger('submit')
    await flushPromises()

    expect(app.mock.history.post).toHaveLength(1)
    expect(JSON.parse(app.mock.history.post[0].data)).toEqual({
      user: 2,
      role: 'member',
    })
  })

  test('previews a workspace before binding it', async () => {
    const organization = {
      id: 'org-1',
      name: 'Acme',
      status: 'active',
      provisioning_status: 'ready',
      members: [
        { id: 1, email: 'owner@example.com', role: 'owner', suspended: false },
      ],
      workspaces: [],
      effective_entitlement: { source: 'manual', seat_limit: 5 },
    }
    app.mock.onGet('/organizations/org-1/').reply(200, organization)
    app.mock.onGet('/organizations/org-1/invitations/').reply(200, [])
    app.mock
      .onGet('/organizations/org-1/workspaces/bind/?workspace=7')
      .reply(200, {
        workspace: 7,
        outsiders: [{ user_id: 9, user__email: 'outsider@example.com' }],
        pending_invitations: [],
      })
    app.mock.onPost('/organizations/org-1/workspaces/bind/').reply(201, {})

    const wrapper = await app.mount(OrganizationDetail, {
      props: { routeOrganizationId: 'org-1' },
    })
    const workspaceForm = wrapper.find('[data-testid="workspace-bind-form"]')
    await workspaceForm.find('input[type="number"]').setValue('7')
    await workspaceForm.trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('outsider@example.com')
    expect(app.mock.history.post).toHaveLength(0)

    await workspaceForm.trigger('submit')
    await flushPromises()
    expect(app.mock.history.post).toHaveLength(1)
  })

  test('removes one member workspace assignment without removing the member', async () => {
    const organization = {
      id: 'org-1',
      name: 'Acme',
      status: 'active',
      provisioning_status: 'ready',
      members: [
        { id: 1, email: 'owner@example.com', role: 'owner', suspended: false },
        { id: 2, email: 'member@example.com', role: 'member', suspended: false },
      ],
      workspaces: [
        {
          id: 4,
          workspace: { id: 7, name: 'Shared data' },
          assigned_members: 1,
          assignments: [
            {
              membership_id: 2,
              email: 'member@example.com',
              permissions: 'VIEWER',
            },
          ],
        },
      ],
      effective_entitlement: { source: 'manual', seat_limit: 5 },
    }
    app.mock.onGet('/organizations/org-1/').reply(200, organization)
    app.mock.onGet('/organizations/org-1/invitations/').reply(200, [])
    app.mock.onDelete('/organizations/org-1/workspaces/4/members/2/').reply(204)

    const wrapper = await app.mount(OrganizationDetail, {
      props: { routeOrganizationId: 'org-1' },
    })
    await wrapper.find('[data-testid="unassign-workspace-member"]').trigger('click')
    await flushPromises()

    expect(app.mock.history.delete).toHaveLength(1)
  })
})
