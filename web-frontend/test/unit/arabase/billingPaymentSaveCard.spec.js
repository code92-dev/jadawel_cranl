import { submitPayment } from '../../../../plugins/jadawel_billing/web-frontend/modules/jadawel-billing/payment.js'

test('payment requests card tokenization only when the payer opts in', async () => {
  const transport = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: 'initiated' }),
  })

  await submitPayment(
    { id: 'order-1', amount: 5000, currency: 'SAR' },
    'pk_test_fixture',
    {
      name: 'Test',
      number: '4111111111111111',
      month: '12',
      year: '2030',
      cvc: '123',
    },
    'https://example.com/billing',
    transport,
    { saveCard: true }
  )

  const body = JSON.parse(transport.mock.calls[0][1].body)
  expect(body.source.save_card).toBe(true)
})

test('payment requests do not ask Moyasar to retain an unchecked card', async () => {
  const transport = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => ({ status: 'paid' }) })

  await submitPayment(
    { id: 'order-2', amount: 5000, currency: 'SAR' },
    'pk_test_fixture',
    {
      name: 'Test',
      number: '4111111111111111',
      month: '12',
      year: '2030',
      cvc: '123',
    },
    'https://example.com/billing',
    transport
  )

  const body = JSON.parse(transport.mock.calls[0][1].body)
  expect(body.source.save_card).toBe(false)
})
