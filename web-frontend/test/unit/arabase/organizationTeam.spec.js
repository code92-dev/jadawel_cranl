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

    const addForm = wrapper.findAll('form')[1]
    await addForm.find('input[type="number"]').setValue('2')
    await addForm.trigger('submit')
    await flushPromises()

    expect(app.mock.history.post).toHaveLength(1)
    expect(JSON.parse(app.mock.history.post[0].data)).toEqual({
      user: 2,
      role: 'member',
    })
  })
})
