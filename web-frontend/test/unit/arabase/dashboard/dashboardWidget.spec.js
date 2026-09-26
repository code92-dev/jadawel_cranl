import { defineComponent } from 'vue'
import { mountSuspended } from '@nuxt/test-utils/runtime'

import ChartWidget from '@jadawel/modules/arabase/dashboard/components/widget/ChartWidget'
import ProgressWidget from '@jadawel/modules/arabase/dashboard/components/widget/ProgressWidget'
import RecordsListWidget from '@jadawel/modules/arabase/dashboard/components/widget/RecordsListWidget'
import UpcomingDatesWidget from '@jadawel/modules/arabase/dashboard/components/widget/UpcomingDatesWidget'
import {
  ChartWidgetType,
  ProgressWidgetType,
  RecordsListWidgetType,
  UpcomingDatesWidgetType,
} from '@jadawel/modules/arabase/dashboard/widgetTypes'
import { WidgetType } from '@jadawel/modules/dashboard/widgetTypes'

/**
 * The plumbing every arabase widget shares: the props it takes, the store
 * getters it reads through `storePrefix`, the context menu in edit mode, the
 * re-emitted `delete-widget`, the misconfiguration badge and the spinner.
 */
const WIDGETS = [
  {
    component: ChartWidget,
    name: 'ChartWidget',
    root: '.dashboard-chart-widget',
    data: { result: { series: [], groups: [], truncated: false } },
    widget: { chart_type: 'bar', series_config: {}, show_legend: true },
  },
  {
    component: ProgressWidget,
    name: 'ProgressWidget',
    root: '.dashboard-progress-widget',
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
    root: '.dashboard-records-list-widget',
    data: { results: [], has_next_page: false },
    widget: { field_ids: [] },
  },
  {
    component: UpcomingDatesWidget,
    name: 'UpcomingDatesWidget',
    root: '.dashboard-upcoming-dates-widget',
    data: { results: [], has_next_page: false },
    widget: { field_ids: [] },
  },
]

const WidgetContextMenuStub = defineComponent({
  name: 'WidgetContextMenu',
  props: {
    widget: { type: Object, required: true },
    dashboard: { type: Object, required: true },
  },
  emits: ['delete-widget'],
  template:
    '<button class="stub-context-menu" @click="$emit(\'delete-widget\', widget)" />',
})

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
    schema: { items: { properties: {} } },
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
          get: () => ({
            getName: () => 'Sum',
            getResult: (ds, result) => result.result,
          }),
        },
      },
      stubs: {
        WidgetContextMenu: WidgetContextMenuStub,
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
    expect(wrapper.find(definition.root).exists()).toBe(true)
    expect(wrapper.find('.widget__header-title').text()).toBe('Widget title')
    expect(wrapper.find('.stub-context-menu').exists()).toBe(false)
    expect(wrapper.find('.stub-badge').exists()).toBe(false)
  })

  test('edit mode shows the context menu and re-emits delete-widget', async () => {
    const wrapper = await mountWidget(definition, { isEditMode: true })

    expect(wrapper.vm.isEditMode).toBe(true)
    await wrapper.get('.stub-context-menu').trigger('click')

    expect(wrapper.emitted('delete-widget')).toHaveLength(1)
    expect(wrapper.emitted('delete-widget')[0][0]).toMatchObject({
      id: 3,
      data_source_id: 7,
    })
  })

  test('an errored data source is flagged as misconfigured', async () => {
    const wrapper = await mountWidget(definition, { error: true })

    expect(wrapper.vm.dataSourceMisconfigured).toBe(true)
    expect(wrapper.find('.stub-badge').text()).toBe('widget.fixConfiguration')
  })

  test('shows only a spinner while loading', async () => {
    const wrapper = await mountWidget(definition, { loading: true })

    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    expect(wrapper.find('.widget__header').exists()).toBe(false)
  })
})

describe('arabase widget types', () => {
  const app = { $i18n: { t: (key) => key } }

  test.each([
    [ChartWidgetType, 'chart', 10],
    [RecordsListWidgetType, 'records_list', 20],
    [ProgressWidgetType, 'progress', 30],
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
})
