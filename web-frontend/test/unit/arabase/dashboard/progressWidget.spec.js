import { mountSuspended } from '@nuxt/test-utils/runtime'

import ProgressWidget from '@jadawel/modules/arabase/dashboard/components/widget/ProgressWidget'

describe('ProgressWidget', () => {
  const dashboard = { id: 1, workspace: { id: 1 } }

  const mountWidget = async ({ widget = {}, result = '50', error = false }) => {
    const dataSource = { id: 7, type: 'local_jadawel_aggregate_rows' }
    const store = {
      getters: {
        'dashboardApplication/getDataSourceById': () => dataSource,
        'dashboardApplication/getDataForDataSource': () =>
          error ? { _error: true } : { result },
        'dashboardApplication/isEditMode': false,
      },
    }

    return await mountSuspended(ProgressWidget, {
      props: {
        dashboard,
        widget: {
          id: 3,
          title: 'Collections',
          description: '',
          type: 'progress',
          data_source_id: 7,
          target_value: '100',
          display_style: 'bar',
          warning_threshold: 50,
          success_threshold: 100,
          ...widget,
        },
      },
      global: {
        mocks: {
          $store: store,
          $registry: {
            get: () => ({ getResult: (ds, data) => data.result }),
          },
        },
        stubs: {
          Badge: { template: '<span><slot /></span>' },
        },
      },
    })
  }

  const percentage = (wrapper) =>
    wrapper
      .find('.widget-progress__percentage, .widget-progress__dial-label')
      .text()

  const fillWidth = (wrapper) =>
    wrapper.find('.widget-progress__fill').attributes('style')

  const tone = (wrapper) =>
    wrapper
      .find('.widget-progress')
      .classes()
      .find((name) => name.startsWith('widget-tone--'))

  const dash = (wrapper) =>
    Number(
      wrapper
        .find('.widget-progress__arc')
        .attributes('stroke-dasharray')
        .split(' ')[0]
    )

  test('the percentage is the result over the target', async () => {
    const wrapper = await mountWidget({ result: '25' })

    expect(percentage(wrapper)).toBe('25%')
    expect(fillWidth(wrapper)).toContain('25%')
  })

  test('overshooting shows above 100% but the bar stops at full', async () => {
    // A bar wider than its track escapes the widget frame, while the number is
    // exactly the information the user wants.
    const wrapper = await mountWidget({ result: '250' })

    expect(percentage(wrapper)).toBe('250%')
    expect(fillWidth(wrapper)).toContain('100%')
  })

  test('the tone and status follow the thresholds', async () => {
    const danger = await mountWidget({ result: '10' })
    expect(tone(danger)).toBe('widget-tone--danger')
    expect(danger.find('.widget-status--danger').text()).toContain(
      'progressWidget.status.atRisk'
    )

    const warning = await mountWidget({ result: '60' })
    expect(tone(warning)).toBe('widget-tone--warning')
    expect(warning.find('.widget-status').text()).toContain(
      'progressWidget.status.onTrack'
    )

    const success = await mountWidget({ result: '100' })
    expect(tone(success)).toBe('widget-tone--success')
    expect(success.find('.widget-status').text()).toContain(
      'progressWidget.status.met'
    )
  })

  test('a non-numeric result shows a dash and no status', async () => {
    const wrapper = await mountWidget({ result: null })

    expect(percentage(wrapper)).toBe('—')
    expect(tone(wrapper)).toBe('widget-tone--neutral')
    expect(wrapper.find('.widget-status').exists()).toBe(false)
  })

  test('a zero target shows a dash instead of Infinity', async () => {
    // The API rejects it, but an imported or API-edited widget could carry one.
    const wrapper = await mountWidget({ widget: { target_value: '0' } })

    expect(percentage(wrapper)).toBe('—')
  })

  test('the value and target follow the number format', async () => {
    const wrapper = await mountWidget({
      result: '1250000',
      widget: {
        target_value: '2000000',
        appearance: { compact: true, suffix: 'SAR' },
      },
    })

    expect(percentage(wrapper)).toBe('63%')
    expect(wrapper.find('.widget-progress__of').text()).toBe(
      'progressWidget.ofTarget'
    )
    expect(wrapper.vm.valueLabel).toBe('\u20C1\u00A01.3M')
    expect(wrapper.vm.targetLabel).toBe('\u20C1\u00A02M')
  })

  test('the bar marks where at risk ends', async () => {
    const wrapper = await mountWidget({ widget: { warning_threshold: 60 } })

    expect(
      wrapper.find('.widget-progress__mark').attributes('style')
    ).toContain('60%')
  })

  test('the ring and the gauge draw an arc instead of a bar', async () => {
    const ring = await mountWidget({
      widget: { display_style: 'ring' },
      result: '50',
    })
    expect(ring.find('.widget-progress__fill').exists()).toBe(false)
    // pathLength is 100, so the dash is the percentage.
    expect(dash(ring)).toBe(50)
    expect(percentage(ring)).toBe('50%')

    const gauge = await mountWidget({
      widget: { display_style: 'gauge' },
      result: '130',
    })
    expect(gauge.find('path.widget-progress__arc').exists()).toBe(true)
    expect(dash(gauge)).toBe(100)
    expect(percentage(gauge)).toBe('130%')
  })

  test('nothing is drawn when the data source is misconfigured', async () => {
    const wrapper = await mountWidget({ error: true })

    expect(wrapper.find('.widget-frame__state').exists()).toBe(true)
    expect(wrapper.find('.widget-progress').exists()).toBe(false)
  })
})
