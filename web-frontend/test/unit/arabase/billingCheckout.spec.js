import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@jadawel/test/helpers/testApp'
import Billing from '../../../../plugins/jadawel_billing/web-frontend/modules/jadawel-billing/pages/billing.vue'

describe('Billing payment recovery', () => {
  let app
  beforeEach(() => {
    app = new TestApp()
  })
  afterEach(async () => {
    await app.afterEach()
  })
  test('verify click does not submit the DOM event as a payment ID', async () => {
    const order = {
      id: 'order-1',
      status: 'pending',
      provider_payment_id: 'payment-1',
      amount: 5000,
      currency: 'SAR',
    }
    app.mock
      .onGet('/billing/checkout/')
      .reply(200, { accounts: [], prices: [], mode: 'test' })
    app.mock.onGet('/billing/orders/').reply(200, [])
    app.mock.onPost('/billing/orders/order-1/verify/').reply(200, order)
    const wrapper = await app.mount(Billing)
    await flushPromises()
    await wrapper.setData({ order, submitted: true })
    const button = wrapper
      .findAll('button')
      .find((item) => item.text().includes('billing.verifyPayment'))
    expect(button).toBeDefined()
    await button.trigger('click')
    await flushPromises()
    expect(app.mock.history.post).toHaveLength(1)
    expect(JSON.parse(app.mock.history.post[0].data)).toEqual({})
  })

  test('loads account access and can cancel a paid renewal', async () => {
    app.mock.onGet('/billing/checkout/').reply(200, {
      accounts: [{ id: 'account-1', kind: 'INDIVIDUAL' }],
      prices: [
        {
          id: 1,
          kind: 'INDIVIDUAL',
          name: 'Personal',
          amount: 5000,
          interval: 'MONTH',
        },
      ],
      mode: 'test',
    })
    app.mock.onGet('/billing/orders/').reply(200, [])
    app.mock.onGet('/billing/accounts/account-1/').reply(200, {
      id: 'account-1',
      effective: { source: 'paid', seat_limit: 1, valid_until: null },
      subscription: {
        price: 1,
        status: 'active',
        seats: 1,
        period_end: '2030-01-01T00:00:00Z',
        cancel_at_period_end: false,
      },
    })
    app.mock
      .onGet('/billing/accounts/account-1/payment-methods/')
      .reply(200, [])
    app.mock
      .onPost('/billing/accounts/account-1/subscription/cancellation/')
      .reply(200, { cancel_at_period_end: true })

    const wrapper = await app.mount(Billing)
    await flushPromises()
    expect(wrapper.find('[data-testid="account-state"]').exists()).toBe(true)

    const button = wrapper
      .findAll('button')
      .find((item) => item.text().includes('billing.cancelRenewal'))
    expect(button).toBeDefined()
    await button.trigger('click')
    await flushPromises()

    expect(app.mock.history.post).toHaveLength(1)
    expect(JSON.parse(app.mock.history.post[0].data)).toEqual({ cancel: true })
  })
})
