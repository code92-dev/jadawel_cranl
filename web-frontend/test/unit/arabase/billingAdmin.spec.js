import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@jadawel/test/helpers/testApp'
import BillingAdmin from '../../../../plugins/jadawel_billing/web-frontend/modules/jadawel-billing/pages/admin.vue'

describe('Billing administration', () => {
  let app
  beforeEach(() => {
    app = new TestApp()
  })
  afterEach(async () => {
    await app.afterEach()
  })

  test('a newly created account appears in the account list', async () => {
    const accounts = []
    app.mock
      .onGet('/billing/admin/accounts/')
      .reply(() => [200, { results: accounts, next: null }])
    app.mock
      .onGet('/billing/admin/plans/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/orders/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/provider-events/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/external-payments/')
      .reply(200, { results: [], next: null })
    app.mock.onPost('/billing/admin/accounts/').reply((config) => {
      const account = { id: 'account-1', ...JSON.parse(config.data) }
      accounts.push(account)
      return [201, account]
    })
    const wrapper = await app.mount(BillingAdmin)
    await flushPromises()
    await wrapper
      .get('[name="responsible_email"]')
      .setValue('owner@example.com')
    await wrapper.get('[data-testid="account-form"]').trigger('submit')
    await flushPromises()
    expect(wrapper.get('[data-testid="account-list"]').text()).toContain(
      'account-1'
    )
  })

  test('staff can reconcile a pending payment from the admin list', async () => {
    const pending = {
      id: 'order-1',
      owner_email: 'owner@example.com',
      payment_id: 'payment-1',
      amount: 5000,
      status: 'pending',
    }
    app.mock
      .onGet('/billing/admin/accounts/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/plans/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/orders/')
      .reply(200, { results: [pending], next: null })
    app.mock
      .onGet('/billing/admin/provider-events/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/external-payments/')
      .reply(200, { results: [], next: null })
    app.mock.onPost('/billing/admin/orders/order-1/reconcile/').reply(200, {
      ...pending,
      status: 'paid',
    })
    const wrapper = await app.mount(BillingAdmin)
    await flushPromises()
    await wrapper.get('[data-testid="payment-list"] button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-testid="payment-list"]').text()).toContain('paid')
  })

  test('staff can record an external payment', async () => {
    app.mock.onGet('/billing/admin/accounts/').reply(200, {
      results: [
        { id: 'account-1', owner_email: 'owner@example.com', kind: 'TEAM' },
      ],
      next: null,
    })
    app.mock
      .onGet('/billing/admin/plans/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/orders/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/provider-events/')
      .reply(200, { results: [], next: null })
    app.mock
      .onGet('/billing/admin/external-payments/')
      .reply(200, { results: [], next: null })
    app.mock.onPost('/billing/admin/external-payments/').reply(201, {
      id: 1,
      account: 'account-1',
      amount: 1500,
      currency: 'SAR',
      reference: 'bank-transfer-1',
      paid_at: '2026-09-08T13:45:00Z',
      notes: '',
      actor: 7,
      created_at: '2026-09-08T13:45:00Z',
    })
    const wrapper = await app.mount(BillingAdmin)
    await flushPromises()
    await wrapper
      .get('[data-testid="external-payment-form"] input[type="number"]')
      .setValue(1500)
    await wrapper
      .get('[data-testid="external-payment-form"] input:not([type])')
      .setValue('bank-transfer-1')
    await wrapper
      .get('[data-testid="external-payment-form"] input[type="datetime-local"]')
      .setValue('2026-09-08T16:45')
    await wrapper.get('[data-testid="external-payment-form"]').trigger('submit')
    await flushPromises()
    expect(
      wrapper.get('[data-testid="external-payment-list"]').text()
    ).toContain('bank-transfer-1')
  })
})
