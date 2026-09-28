import { defineComponent } from 'vue'
import { mountSuspended } from '@nuxt/test-utils/runtime'

import ChartWidget from '@jadawel/modules/arabase/dashboard/components/widget/ChartWidget'
import KpiWidget from '@jadawel/modules/arabase/dashboard/components/widget/KpiWidget'
import ProgressWidget from '@jadawel/modules/arabase/dashboard/components/widget/ProgressWidget'
import RecordsListWidget from '@jadawel/modules/arabase/dashboard/components/widget/RecordsListWidget'
import UpcomingDatesWidget from '@jadawel/modules/arabase/dashboard/components/widget/UpcomingDatesWidget'
import {
  ChartWidgetType,
  KpiWidgetType,
  ProgressWidgetType,
  RecordsListWidgetType,
  TextWidgetType,
  UpcomingDatesWidgetType,
} from '@jadawel/modules/arabase/dashboard/widgetTypes'
import { WidgetType } from '@jadawel/modules/dashboard/widgetTypes'

/**
 * The plumbing every arabase widget shares: the props it takes, the store
 * getters it reads through `storePrefix`, the frame's title, the
 * misconfiguration badge and note, and the skeleton while loading. Moving,
 * resizing and deleting belong to the board's edit chrome, not the widget.
 */
const WIDGETS = [
  {
    component: KpiWidget,
    name: 'KpiWidget',
    body: '.widget-kpi',
    data: { result: '1610000' },
    widget: {},
  },
  {
    component: ChartWidget,
    name: 'ChartWidget',
    body: '.widget-chart',
    data: {
      result: {
        series: [{ key: 'k', label: 'Amount', data: [3] }],
        groups: [{ value: 'A' }],
        truncated: false,
      },
    },
    widget: { chart_type: 'bar', series_config: {}, show_legend: true },
  },
  {
    component: ProgressWidget,
    name: 'ProgressWidget',
    body: '.widget-progress',
    data: { result: '50' },
    widget: {
      target_value: '100',
      display_style: 'bar',
      warning_threshold: 50,
      success_threshold: 100,
    },
  },
  {
    component: RecordsListWidget,
    name: 'RecordsListWidget',
    body: '.widget-table',
    data: { results: [{ id: 1, Name: 'A' }], has_next_page: false },
    widget: { field_ids: [] },
  },
  {
    component: UpcomingDatesWidget,
    name: 'UpcomingDatesWidget',
    body: '.widget-agenda',
    data: { results: [{ id: 1, Name: 'A' }], has_next_page: false },
    widget: { field_ids: [] },
  },
]

const chartStub = defineComponent({
  props: { data: Object, options: Object },
  template: '<div class="chart-stub" />',
})

const mountWidget = async (
  { component, data, widget },
  { storePrefix, isEditMode = false, error = false, loading = false } = {}
) => {
  const prefix = storePrefix || ''
  // The data source is looked up by the widget's data_source_id, and its data
  // by the data source's own id, so the two ids differ here on purpose.
  const dataSource = {
    id: 70,
    type: 'local_jadawel_list_rows',
    schema: { items: { properties: { field_1: { title: 'Name' } } } },
  }
  const store = {
    getters: {
      [`${prefix}dashboardApplication/getDataSourceById`]: (id) =>
        id === 7 ? dataSource : null,
      [`${prefix}dashboardApplication/getDataForDataSource`]: (id) => {
        if (id !== 70) {
          return null
        }
        return error ? { _error: true } : data
      },
      [`${prefix}dashboardApplication/isEditMode`]: isEditMode,
      'application/getAll': [],
    },
  }

  const props = {
    dashboard: { id: 1, workspace: { id: 1 } },
    widget: {
      id: 3,
      title: 'Widget title',
      description: '',
      data_source_id: 7,
      ...widget,
    },
    loading,
  }
  if (storePrefix !== undefined) {
    props.storePrefix = storePrefix
  }

  return await mountSuspended(component, {
    props,
    global: {
      mocks: {
        $store: store,
        $registry: {
          exists: () => true,
          get: () => ({
            getName: () => 'Sum',
            getResult: (ds, result) => result.result,
          }),
        },
      },
      stubs: {
        Badge: { template: '<span class="stub-badge"><slot /></span>' },
        BarChart: chartStub,
        LineChart: chartStub,
        PieChart: chartStub,
        DoughnutChart: chartStub,
      },
    },
  })
}

describe.each(WIDGETS)('$name shared widget contract', (definition) => {
  test('keeps its name, props and emitted events', async () => {
    const wrapper = await mountWidget(definition)

    expect(definition.component.name).toBe(definition.name)
    expect(Object.keys(wrapper.vm.$options.props)).toEqual(
      expect.arrayContaining(['dashboard', 'widget', 'storePrefix', 'loading'])
    )
    expect(wrapper.vm.$options.emits).toEqual(['delete-widget'])
    expect(wrapper.vm.storePrefix).toBe('')
    expect(wrapper.vm.loading).toBe(false)
  })

  test('reads the store through the prefix and chains the data source id', async () => {
    const wrapper = await mountWidget(definition, { storePrefix: 'public/' })

    expect(wrapper.vm.dataSource.id).toBe(70)
    expect(wrapper.vm.dataForDataSource).toEqual(definition.data)
    expect(wrapper.vm.isEditMode).toBe(false)
    expect(wrapper.vm.dataSourceMisconfigured).toBe(false)
    expect(wrapper.find('.widget-frame').exists()).toBe(true)
    expect(wrapper.find(definition.body).exists()).toBe(true)
    expect(wrapper.find('.widget-frame__title').text()).toBe('Widget title')
    expect(wrapper.find('.stub-badge').exists()).toBe(false)
  })

  test('the header is the drag handle the board looks for', async () => {
    const wrapper = await mountWidget(definition, { isEditMode: true })

    expect(wrapper.find('.widget-frame__header.widget__header').exists()).toBe(
      true
    )
  })

  test('an errored data source is flagged as misconfigured', async () => {
    const wrapper = await mountWidget(definition, { error: true })

    expect(wrapper.vm.dataSourceMisconfigured).toBe(true)
    expect(wrapper.find('.stub-badge').text()).toBe('widget.fixConfiguration')
    expect(wrapper.find('.widget-frame__state').exists()).toBe(true)
    expect(wrapper.find(definition.body).exists()).toBe(false)
    // The hint to open the settings is only useful to someone editing.
    expect(wrapper.find('.widget-frame__state-hint').exists()).toBe(false)
  })

  test('a misconfigured widget tells an editor where to fix it', async () => {
    const wrapper = await mountWidget(definition, {
      error: true,
      isEditMode: true,
    })

    expect(wrapper.find('.widget-frame__state-hint').exists()).toBe(true)
  })

  test('keeps its title and shows a skeleton while loading', async () => {
    const wrapper = await mountWidget(definition, { loading: true })

    expect(wrapper.find('.widget-frame__title').text()).toBe('Widget title')
    expect(wrapper.find('.widget-frame__skeleton').exists()).toBe(true)
    expect(wrapper.find(definition.body).exists()).toBe(false)
    expect(wrapper.find('.stub-badge').exists()).toBe(false)
  })
})

describe('arabase widget types', () => {
  const app = { $i18n: { t: (key) => key } }

  test.each([
    [ChartWidgetType, 'chart', 10],
    [RecordsListWidgetType, 'records_list', 20],
    [ProgressWidgetType, 'progress', 5],
    [UpcomingDatesWidgetType, 'upcoming_dates', 40],
  ])(
    '%s keeps its type and order and loads until dispatched',
    (Type, type, order) => {
      const widgetType = new Type({ app })
      const widget = { id: 3, data_source_id: 7 }

      expect(widgetType).toBeInstanceOf(WidgetType)
      expect(Type.getType()).toBe(type)
      expect(widgetType.type).toBe(type)
      expect(widgetType.getOrder()).toBe(order)
      expect(widgetType.isLoading(widget, {})).toBe(true)
      expect(widgetType.isLoading(widget, { 7: {} })).toBe(true)
      expect(widgetType.isLoading(widget, { 8: { result: 1 } })).toBe(true)
      expect(widgetType.isLoading(widget, { 7: { result: 1 } })).toBe(false)
      expect(widgetType.isLoading(widget, { 7: { _error: true } })).toBe(false)
    }
  )

  test('the key number replaces summary under the same type name', () => {
    const widgetType = new KpiWidgetType({ app })

    expect(KpiWidgetType.getType()).toBe('summary')
    expect(widgetType.getOrder()).toBe(0)
    expect(widgetType.name).toBe('kpiWidget.name')
    expect(widgetType.isLoading({ data_source_id: 7 }, {})).toBe(true)
    expect(
      widgetType.isLoading({ data_source_id: 7 }, { 7: { result: 1 } })
    ).toBe(false)
  })

  test('a text widget never waits for data and a section has no card', () => {
    const widgetType = new TextWidgetType({ app })

    expect(TextWidgetType.getType()).toBe('text')
    expect(widgetType.isLoading({ id: 3 }, {})).toBe(false)
    expect(widgetType.isBare({ text_style: 'section' })).toBe(true)
    expect(widgetType.isBare({ text_style: 'note' })).toBe(false)
  })

  test('every variation says where it is listed and the size it starts at', () => {
    const types = [
      KpiWidgetType,
      ProgressWidgetType,
      ChartWidgetType,
      RecordsListWidgetType,
      UpcomingDatesWidgetType,
      TextWidgetType,
    ].map((Type) => new Type({ app }))
    const variations = types.flatMap((type) => type.variations)

    expect(variations).toHaveLength(14)
    for (const variation of variations) {
      expect(['numbers', 'charts', 'lists', 'text']).toContain(
        variation.category
      )
      expect(variation.size.width).toBeGreaterThanOrEqual(
        variation.type.minSize.width
      )
      expect(variation.size.height).toBeGreaterThanOrEqual(
        variation.type.minSize.height
      )
      expect(variation.size.width).toBeLessThanOrEqual(12)
    }
    const kpi = variations.find((v) => v.type instanceof KpiWidgetType)
    expect(kpi.size).toEqual({ width: 3, height: 2 })
    const section = variations.find((v) => v.params.text_style === 'section')
    expect(section.size).toEqual({ width: 12, height: 1 })
  })
})
