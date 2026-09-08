import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@jadawel/test/helpers/testApp'
import GrantPanel from '../../../../plugins/jadawel_billing/web-frontend/modules/jadawel-billing/components/GrantPanel.vue'

describe('Complimentary access', () => {
  let app
  beforeEach(() => {
    app = new TestApp()
  })
  afterEach(async () => {
    await app.afterEach()
  })
  test('admin reviews a grant before saving and sees effective access', async () => {
    const url = '/billing/admin/accounts/account-1/grant/'
    app.mock.onGet(url).reply(200, {
      grant: null,
      effective: { source: 'restricted', seat_limit: 0 },
    })
    app.mock
      .onGet('/billing/admin/accounts/account-1/audit/')
      .reply(200, { results: [] })
    app.mock.onPost(url + 'preview/').reply(200, {
      plan: 1,
      seat_limit: 12,
      starts_at: new Date().toISOString(),
      expires_at: null,
      reason: 'Partner access',
    })
    app.mock.onPut(url).reply(200, {
      grant: null,
      effective: { source: 'manual', seat_limit: 12 },
    })
    const wrapper = await app.mount(GrantPanel, {
      props: {
        account: { id: 'account-1', kind: 'TEAM' },
        plans: [{ id: 1, name: 'Team', kind: 'TEAM' }],
      },
    })
    await flushPromises()
    await wrapper.get('[name="plan"]').setValue('1')
    await wrapper.get('[name="seats"]').setValue(12)
    await wrapper.get('[name="reason"]').setValue('Partner access')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(app.mock.history.put).toHaveLength(0)
    await wrapper.get('[data-testid="confirm-grant"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-testid="effective-access"]').text()).toContain(
      '12'
    )
  })
})
