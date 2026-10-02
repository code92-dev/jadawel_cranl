import { TestApp } from '@jadawel/test/helpers/testApp'
import DashboardAreaChart from '@jadawel/modules/core/components/dashboard/DashboardAreaChart'

describe('DashboardAreaChart', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('gives the plotted values to assistive technology without stretching the page', async () => {
    const series = Array.from({ length: 30 }, (_, index) => ({
      date: `2026-09-${String(index + 1).padStart(2, '0')}`,
      count: index,
    }))
    const wrapper = await testApp.mount(DashboardAreaChart, {
      props: { title: 'Rows added', series, emptyMessage: 'Nothing yet' },
    })

    // A table ignores the 1px box that hides it, so its rows would extend the
    // page; the hiding is on a wrapper, which honours it.
    const hidden = wrapper.get('.chart__sr-only')
    expect(hidden.element.tagName).toBe('DIV')
    expect(hidden.findAll('tbody tr')).toHaveLength(30)
    expect(wrapper.find('table.chart__sr-only').exists()).toBe(false)
  })
})
