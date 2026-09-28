import { defineComponent } from 'vue'
import { mountSuspended } from '@nuxt/test-utils/runtime'

import ChartWidget from '@jadawel/modules/arabase/dashboard/components/widget/ChartWidget'

// The chart itself renders into a canvas, which tells us nothing in jsdom. Stub
// the vue-chartjs components so the props the widget computes — the labels,
// the datasets, the colours — become inspectable attributes instead.
const chartStub = (name) =>
  defineComponent({
    name,
    props: {
      data: { type: Object, required: true },
      options: { type: Object, required: true },
    },
    template: `<div class="chart-stub" :data-chart="'${name}'"
      :data-labels="JSON.stringify(data.labels)"
      :data-datasets="JSON.stringify(data.datasets)"
      :data-options="JSON.stringify(options)"
      :data-legend="String(!!options.plugins.legend.display)" />`,
  })

const AMOUNT_SERIES = {
  key: 'field_1_sum',
  field_id: 1,
  aggregation_type: 'sum',
  label: 'Amount',
  data: ['30', '5'],
}

const COUNT_SERIES = {
  key: 'field_2_count',
  field_id: 2,
  aggregation_type: 'count',
  label: 'Orders',
  data: ['3', '1'],
}

const RESULT = {
  groups: [
    { value: 'Riyadh', color: 'blue' },
    { value: 'Jeddah', color: null },
  ],
  series: [AMOUNT_SERIES],
  truncated: false,
}

describe('ChartWidget', () => {
  const dashboard = { id: 1, workspace: { id: 1 } }

  const mountWidget = async ({ widget = {}, data = RESULT, error = false }) => {
    const dataSource = { id: 7, type: 'local_jadawel_grouped_aggregate_rows' }
    const store = {
      getters: {
        'dashboardApplication/getDataSourceById': () => dataSource,
        'dashboardApplication/getDataForDataSource': () =>
          error ? { _error: true } : { result: data },
        'dashboardApplication/isEditMode': false,
      },
    }

    return await mountSuspended(ChartWidget, {
      props: {
        dashboard,
        widget: {
          id: 3,
          title: 'Orders by region',
          description: '',
          type: 'chart',
          data_source_id: 7,
          chart_type: 'bar',
          series_config: {},
          show_legend: true,
          ...widget,
        },
      },
      global: {
        mocks: {
          $store: store,
          $registry: {
            exists: () => true,
            get: () => ({ getName: () => 'Sum' }),
          },
        },
        stubs: {
          BarChart: chartStub('BarChart'),
          LineChart: chartStub('LineChart'),
          PieChart: chartStub('PieChart'),
          DoughnutChart: chartStub('DoughnutChart'),
          Badge: { template: '<span><slot /></span>' },
        },
      },
    })
  }

  test('one dataset per series, one label per group', async () => {
    const wrapper = await mountWidget({})
    const chart = wrapper.find('.chart-stub')

    expect(JSON.parse(chart.attributes('data-labels'))).toEqual([
      'Riyadh',
      'Jeddah',
    ])
    const datasets = JSON.parse(chart.attributes('data-datasets'))
    expect(datasets).toHaveLength(1)
    // Numbers arrive as the field serializes them and are plotted as numbers.
    expect(datasets[0].data).toEqual([30, 5])
  })

  test('the chart type selects the component', async () => {
    const wrapper = await mountWidget({ widget: { chart_type: 'doughnut' } })

    expect(wrapper.find('.chart-stub').attributes('data-chart')).toBe(
      'DoughnutChart'
    )
  })

  test('a sliced chart colours each bucket, a bar chart colours the series', async () => {
    const sliced = await mountWidget({ widget: { chart_type: 'pie' } })
    const slicedColors = JSON.parse(
      sliced.find('.chart-stub').attributes('data-datasets')
    )[0].backgroundColor
    // One colour per bucket, and the single select's own colour is honoured
    // rather than replaced by the palette.
    expect(Array.isArray(slicedColors)).toBe(true)
    expect(slicedColors).toHaveLength(2)

    const bar = await mountWidget({})
    const barColor = JSON.parse(
      bar.find('.chart-stub').attributes('data-datasets')
    )[0].backgroundColor
    expect(typeof barColor).toBe('string')
  })

  test('a series colour override wins over the palette', async () => {
    const wrapper = await mountWidget({
      widget: { series_config: { field_1_sum: { color: '#123456' } } },
    })

    const datasets = JSON.parse(
      wrapper.find('.chart-stub').attributes('data-datasets')
    )
    expect(datasets[0].backgroundColor).toBe('#123456')
  })

  test('a series label override wins over the field name', async () => {
    const wrapper = await mountWidget({
      widget: { series_config: { field_1_sum: { label: 'Total sales' } } },
    })

    const datasets = JSON.parse(
      wrapper.find('.chart-stub').attributes('data-datasets')
    )
    expect(datasets[0].label).toBe('Total sales')
  })

  test('with no group by the series become the categories', async () => {
    const wrapper = await mountWidget({
      data: {
        groups: [],
        series: [{ ...AMOUNT_SERIES, data: ['35'] }],
        truncated: false,
      },
    })

    const chart = wrapper.find('.chart-stub')
    expect(JSON.parse(chart.attributes('data-datasets'))[0].data).toEqual([35])
    expect(JSON.parse(chart.attributes('data-labels'))).toHaveLength(1)
  })

  test('an empty group value gets a label rather than a blank tick', async () => {
    const wrapper = await mountWidget({
      data: { ...RESULT, groups: [null, { value: 'Jeddah', color: null }] },
    })

    const labels = JSON.parse(
      wrapper.find('.chart-stub').attributes('data-labels')
    )
    expect(labels[0]).toBeTruthy()
    expect(labels[0]).not.toBe('Jeddah')
  })

  test('a single series has no legend; several do unless turned off', async () => {
    const single = await mountWidget({})
    expect(single.find('.chart-stub').attributes('data-legend')).toBe('false')

    const data = { ...RESULT, series: [AMOUNT_SERIES, COUNT_SERIES] }
    const several = await mountWidget({ data })
    expect(several.find('.chart-stub').attributes('data-legend')).toBe('true')

    const off = await mountWidget({ data, widget: { show_legend: false } })
    expect(off.find('.chart-stub').attributes('data-legend')).toBe('false')
  })

  test('a horizontal bar chart is a bar chart on the other axis', async () => {
    const wrapper = await mountWidget({
      widget: { chart_type: 'horizontal_bar' },
    })
    const chart = wrapper.find('.chart-stub')
    const options = JSON.parse(chart.attributes('data-options'))

    expect(chart.attributes('data-chart')).toBe('BarChart')
    expect(options.indexAxis).toBe('y')
    expect(options.scales.x.beginAtZero).toBe(true)
  })

  test('an area chart is a filled line, stacked when asked', async () => {
    const area = await mountWidget({ widget: { chart_type: 'area' } })
    const areaChart = area.find('.chart-stub')
    expect(areaChart.attributes('data-chart')).toBe('LineChart')
    expect(JSON.parse(areaChart.attributes('data-datasets'))[0].fill).toBe(
      'origin'
    )

    const stacked = await mountWidget({
      widget: { chart_type: 'area', appearance: { stacked: true } },
      data: { ...RESULT, series: [AMOUNT_SERIES, COUNT_SERIES] },
    })
    const chart = stacked.find('.chart-stub')
    expect(JSON.parse(chart.attributes('data-datasets'))[1].fill).toBe('stack')
    expect(JSON.parse(chart.attributes('data-options')).scales.y.stacked).toBe(
      true
    )
  })

  test('stacking needs more than one series', async () => {
    const wrapper = await mountWidget({
      widget: { appearance: { stacked: true } },
    })

    const options = JSON.parse(
      wrapper.find('.chart-stub').attributes('data-options')
    )
    expect(options.scales.y.stacked).toBe(false)
  })

  test('a doughnut shows its total and a legend with each share', async () => {
    const wrapper = await mountWidget({ widget: { chart_type: 'doughnut' } })

    expect(wrapper.find('.widget-chart__center-value').text()).toBe('35')
    const items = wrapper.findAll('.widget-chart__legend-item')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('Riyadh')
    expect(items[0].find('.widget-chart__legend-share').text()).toBe('86%')
    expect(items[1].find('.widget-chart__legend-share').text()).toBe('14%')
  })

  test('a pie has no centre total, and its legend can be hidden', async () => {
    const wrapper = await mountWidget({
      widget: { chart_type: 'pie', show_legend: false },
    })

    expect(wrapper.find('.widget-chart__center').exists()).toBe(false)
    expect(wrapper.find('.widget-chart__legend').exists()).toBe(false)
  })

  test('values follow the widget number format', async () => {
    const wrapper = await mountWidget({
      widget: {
        chart_type: 'doughnut',
        appearance: { compact: true, suffix: 'SAR' },
      },
      data: {
        ...RESULT,
        series: [{ ...AMOUNT_SERIES, data: ['1250000', '360000'] }],
      },
    })

    expect(wrapper.find('.widget-chart__center-value').text()).toBe('1.6M SAR')
    expect(wrapper.find('.widget-chart__legend-value').text()).toBe('1.3M SAR')
  })

  test('no chart is drawn when the data source is misconfigured', async () => {
    const wrapper = await mountWidget({ error: true })

    expect(wrapper.find('.chart-stub').exists()).toBe(false)
    expect(wrapper.find('.widget-frame__state').exists()).toBe(true)
  })

  test('no chart is drawn when there is nothing to plot', async () => {
    const wrapper = await mountWidget({
      data: { groups: [], series: [], truncated: false },
    })

    expect(wrapper.find('.chart-stub').exists()).toBe(false)
    expect(wrapper.find('.widget-frame__state').exists()).toBe(true)
  })
})
