import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'
import flushPromises from 'flush-promises'

import GroupedAggregateRowsDataSourceForm from '@jadawel/modules/arabase/dashboard/components/data_source/GroupedAggregateRowsDataSourceForm'

const fetchAll = vi.fn()

vi.mock('@jadawel/modules/database/services/field', () => ({
  default: () => ({ fetchAll }),
}))

const FIELDS_BY_TABLE = {
  11: [
    { id: 101, name: 'Amount', type: 'number' },
    { id: 102, name: 'Region', type: 'text' },
  ],
  12: [],
  21: [
    { id: 201, name: 'Cost', type: 'number' },
    { id: 202, name: 'Note', type: 'text' },
  ],
}

const INTEGRATION = {
  id: 9,
  context_data: {
    databases: [
      {
        id: 1,
        name: 'Sales',
        tables: [
          { id: 11, name: 'Orders' },
          { id: 12, name: 'Customers' },
        ],
        views: [
          { id: 5, name: 'All orders', table_id: 11 },
          { id: 6, name: 'All customers', table_id: 12 },
        ],
      },
      {
        id: 2,
        name: 'Operations',
        tables: [{ id: 21, name: 'Costs' }],
        views: [{ id: 7, name: 'All costs', table_id: 21 }],
      },
    ],
  },
}

// `distribution` is compatible with everything but unsupported by the service,
// so a seeded series must skip it; `sum` only applies to numbers.
const aggregation = (type, isCompatible) => ({
  getType: () => type,
  getName: () => type,
  fieldIsCompatible: isCompatible,
})
const AGGREGATIONS = [
  aggregation('distribution', () => true),
  aggregation('sum', (field) => field.type === 'number'),
  aggregation('count', () => true),
]

const SAVED_VALUES = {
  table_id: 11,
  view_id: 5,
  aggregation_series: [{ field_id: 101, aggregation_type: 'sum' }],
  aggregation_group_bys: [{ field_id: 102 }],
}

const stubs = {
  FormSection: {
    props: ['title'],
    template:
      '<section class="stub-section" :data-title="title"><slot /></section>',
  },
  FormGroup: {
    props: ['label'],
    template: '<div class="stub-group" :data-label="label"><slot /></div>',
  },
  Dropdown: {
    props: ['modelValue', 'disabled', 'error'],
    template: '<div class="stub-dropdown"><slot /></div>',
  },
  DropdownSection: {
    props: ['title'],
    template:
      '<div class="stub-dropdown-section" :data-title="title"><slot /></div>',
  },
  DropdownItem: {
    props: ['name', 'value'],
    template:
      '<div class="stub-dropdown-item" :data-value="String(value)">{{ name }}</div>',
  },
  ButtonText: { template: '<button class="stub-button"><slot /></button>' },
}

/**
 * Every `values-changed` payload is the form's live `values` object, so it is
 * copied at emit time: otherwise each recorded emit would show the final state.
 */
const mountForm = async ({ values = SAVED_VALUES, dataSource = {} } = {}) => {
  const emitted = []
  const wrapper = await mountSuspended(GroupedAggregateRowsDataSourceForm, {
    props: {
      dashboard: { id: 1, workspace: { id: 1 } },
      widget: { id: 3, data_source_id: 7 },
      dataSource: { id: 7, integration_id: 9, ...dataSource },
      defaultValues: values,
      onValuesChanged: (payload) =>
        emitted.push(JSON.parse(JSON.stringify(payload))),
    },
    global: {
      mocks: {
        $client: {},
        $t: (key) => key,
        $store: {
          getters: {
            'dashboardApplication/getIntegrationById': (id) =>
              id === INTEGRATION.id ? INTEGRATION : null,
          },
        },
        $registry: {
          get: (namespace, type) =>
            namespace === 'service'
              ? { unsupportedAggregationTypes: ['distribution'] }
              : { iconClass: `icon-${type}` },
          getOrderedList: () => AGGREGATIONS,
        },
      },
      stubs,
    },
  })
  await flushPromises()
  return { wrapper, emitted }
}

const sectionTitles = (wrapper) =>
  wrapper
    .findAll('.stub-dropdown-section')
    .map((section) => section.attributes('data-title'))

describe('GroupedAggregateRowsDataSourceForm', () => {
  beforeEach(() => {
    fetchAll.mockReset()
    fetchAll.mockImplementation(async (tableId) => ({
      data: FIELDS_BY_TABLE[tableId] || [],
    }))
  })

  test('mounting with saved values loads the fields and emits nothing', async () => {
    const { wrapper, emitted } = await mountForm()

    expect(fetchAll).toHaveBeenCalledTimes(1)
    expect(fetchAll).toHaveBeenCalledWith(11)
    expect(wrapper.vm.tableFields.map((field) => field.id)).toEqual([101, 102])
    expect(wrapper.vm.fieldsLoading).toBe(false)
    expect(wrapper.vm.tableIdHasChanged).toBe(false)
    expect(wrapper.vm.values).toEqual(SAVED_VALUES)
    expect(wrapper.vm.groupByFieldId).toBe(102)
    expect(emitted).toEqual([])
    expect(wrapper.emitted('values-changed')).toBeUndefined()
    expect(wrapper.vm.isFormValid()).toBe(true)
    expect(wrapper.vm.fieldHasErrors('table_id')).toBe(false)
  })

  test('lists every table by database and the views of the chosen table', async () => {
    const { wrapper } = await mountForm()

    expect(wrapper.vm.tableIds).toEqual([11, 12, 21])
    expect(sectionTitles(wrapper)).toEqual(['Sales (1)', 'Operations (2)'])
    expect(wrapper.vm.databaseSelected.id).toBe(1)
    expect(wrapper.vm.tableViews.map((view) => view.id)).toEqual([5])
    const items = wrapper
      .findAll('.stub-dropdown-item')
      .map((item) => item.text())
    expect(items).toEqual(
      expect.arrayContaining(['Orders', 'Customers', 'Costs', 'All orders'])
    )
    expect(items).not.toContain('All customers')
    expect(items).not.toContain('All costs')
    expect(wrapper.findAll('.grouped-aggregate-series')).toHaveLength(1)
  })

  test('changing the table clears the view, series and group bys, then seeds one series', async () => {
    let resolveFields
    fetchAll.mockImplementation(
      (tableId) =>
        new Promise((resolve) => {
          resolveFields = () => resolve({ data: FIELDS_BY_TABLE[tableId] })
        })
    )
    const { wrapper, emitted } = await mountForm()
    resolveFields()
    await flushPromises()

    wrapper.vm.computedTableId = 21

    // The setter clears everything that pointed at the old table at once.
    expect(wrapper.vm.values).toEqual({
      table_id: 21,
      view_id: null,
      aggregation_series: [],
      aggregation_group_bys: [],
    })
    expect(wrapper.vm.tableIdHasChanged).toBe(true)

    await flushPromises()
    expect(fetchAll).toHaveBeenLastCalledWith(21)
    expect(wrapper.vm.fieldsLoading).toBe(true)
    expect(wrapper.vm.tableIdHasChanged).toBe(true)
    expect(emitted).toEqual([
      {
        table_id: 21,
        view_id: null,
        aggregation_series: [],
        aggregation_group_bys: [],
      },
    ])

    resolveFields()
    await flushPromises()

    expect(wrapper.vm.fieldsLoading).toBe(false)
    expect(wrapper.vm.tableIdHasChanged).toBe(false)
    expect(wrapper.vm.values.aggregation_series).toEqual([
      { field_id: 201, aggregation_type: 'sum' },
    ])
    expect(emitted).toEqual([
      {
        table_id: 21,
        view_id: null,
        aggregation_series: [],
        aggregation_group_bys: [],
      },
      {
        table_id: 21,
        view_id: null,
        aggregation_series: [{ field_id: 201, aggregation_type: 'sum' }],
        aggregation_group_bys: [],
      },
    ])
    expect(wrapper.vm.tableViews.map((view) => view.id)).toEqual([7])
  })

  test('a new table without fields seeds no series', async () => {
    const { wrapper, emitted } = await mountForm()

    wrapper.vm.computedTableId = 12
    await flushPromises()

    expect(fetchAll).toHaveBeenLastCalledWith(12)
    expect(wrapper.vm.tableIdHasChanged).toBe(false)
    expect(wrapper.vm.values.aggregation_series).toEqual([])
    expect(emitted).toEqual([
      {
        table_id: 12,
        view_id: null,
        aggregation_series: [],
        aggregation_group_bys: [],
      },
    ])
    expect(wrapper.findAll('.grouped-aggregate-series')).toHaveLength(0)
  })

  test('choosing the table that is already selected changes nothing', async () => {
    const { wrapper, emitted } = await mountForm()

    wrapper.vm.computedTableId = 11
    await flushPromises()

    expect(wrapper.vm.tableIdHasChanged).toBe(false)
    expect(wrapper.vm.values).toEqual(SAVED_VALUES)
    expect(fetchAll).toHaveBeenCalledTimes(1)
    expect(emitted).toEqual([])
  })

  test('group by and series edits emit the whole value set', async () => {
    const { wrapper, emitted } = await mountForm()

    wrapper.vm.groupByFieldId = null
    await flushPromises()
    wrapper.vm.addSeries()
    await flushPromises()

    expect(emitted).toEqual([
      { ...SAVED_VALUES, aggregation_group_bys: [] },
      {
        ...SAVED_VALUES,
        aggregation_series: [
          { field_id: 101, aggregation_type: 'sum' },
          { field_id: 101, aggregation_type: 'sum' },
        ],
        aggregation_group_bys: [],
      },
    ])
    expect(wrapper.emitted('values-changed')).toHaveLength(2)
  })

  test('a new data source resets the form to its values without emitting', async () => {
    const { wrapper, emitted } = await mountForm()
    const nextValues = {
      table_id: 21,
      view_id: 7,
      aggregation_series: [{ field_id: 202, aggregation_type: 'count' }],
      aggregation_group_bys: [],
    }

    await wrapper.setProps({
      dataSource: { id: 8, integration_id: 9 },
      defaultValues: nextValues,
    })
    await flushPromises()

    expect(wrapper.vm.values).toEqual(nextValues)
    expect(fetchAll).toHaveBeenLastCalledWith(21)
    // The reset is not a table change, so the saved series is kept.
    expect(wrapper.vm.tableIdHasChanged).toBe(false)
    expect(wrapper.vm.values.aggregation_series).toEqual([
      { field_id: 202, aggregation_type: 'count' },
    ])
    expect(emitted).toEqual([])
    expect(wrapper.vm.emitValues).toBe(true)
  })

  test('a table that is not in the integration is invalid', async () => {
    const { wrapper } = await mountForm({
      values: { ...SAVED_VALUES, table_id: 999 },
    })

    expect(wrapper.vm.isFormValid()).toBe(false)
    expect(wrapper.vm.fieldHasErrors('table_id')).toBe(true)
    expect(wrapper.vm.v$.values.table_id.isValidTableId.$invalid).toBe(true)
    expect(wrapper.vm.v$.values.table_id.required.$invalid).toBe(false)
    // Everything below the table picker needs a valid table.
    expect(wrapper.findAll('.stub-group')).toHaveLength(1)
    expect(wrapper.findAll('.stub-section')).toHaveLength(1)
  })

  test('a missing table is invalid', async () => {
    const { wrapper } = await mountForm({
      values: { ...SAVED_VALUES, table_id: null },
    })

    expect(fetchAll).not.toHaveBeenCalled()
    expect(wrapper.vm.isFormValid()).toBe(false)
    expect(wrapper.vm.fieldHasErrors('table_id')).toBe(true)
    expect(wrapper.vm.v$.values.table_id.required.$invalid).toBe(true)
  })

  test('keeps its name, props and form events', async () => {
    // mountSuspended renames its clone, so the name is read off the definition
    // and the merged mixin options off the mounted instance.
    const { wrapper } = await mountForm()

    expect(GroupedAggregateRowsDataSourceForm.name).toBe(
      'GroupedAggregateRowsDataSourceForm'
    )
    expect(Object.keys(wrapper.vm.$options.props)).toEqual(
      expect.arrayContaining([
        'dashboard',
        'widget',
        'dataSource',
        'storePrefix',
        'defaultValues',
        'disabled',
      ])
    )
    expect(wrapper.vm.$options.emits).toEqual(['submitted', 'values-changed'])
  })
})
