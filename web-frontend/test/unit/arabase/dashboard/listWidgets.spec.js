import { mountSuspended } from '@nuxt/test-utils/runtime'

import RecordsListWidget from '@jadawel/modules/arabase/dashboard/components/widget/RecordsListWidget'
import UpcomingDatesWidget from '@jadawel/modules/arabase/dashboard/components/widget/UpcomingDatesWidget'

const SCHEMA = {
  items: {
    properties: {
      field_1: { title: 'Name' },
      field_2: { title: 'Region' },
      field_3: { title: 'Due' },
      field_4: {
        title: 'Stage',
        original_type: 'single_select',
        metadata: {},
      },
      field_5: {
        title: 'Amount',
        original_type: 'number',
        metadata: { number_decimal_places: 2 },
      },
    },
  },
}

const mountListWidget = async (
  component,
  { widget = {}, dataSource = {}, results = [], error = false }
) => {
  const source = {
    id: 7,
    type: 'local_jadawel_list_rows',
    schema: SCHEMA,
    ...dataSource,
  }
  const store = {
    getters: {
      'dashboardApplication/getDataSourceById': () => source,
      'dashboardApplication/getDataForDataSource': () =>
        error ? { _error: true } : { results, has_next_page: false },
      'dashboardApplication/isEditMode': false,
      'application/getAll': [
        { id: 40, type: 'database', tables: [{ id: 12 }] },
      ],
    },
  }

  return await mountSuspended(component, {
    props: {
      dashboard: { id: 1, workspace: { id: 1 } },
      widget: {
        id: 3,
        title: 'Latest',
        description: '',
        data_source_id: 7,
        field_ids: [],
        ...widget,
      },
    },
    global: {
      mocks: { $store: store },
      stubs: {
        NuxtLink: {
          props: ['to'],
          template:
            '<a class="stub-link" :data-to="JSON.stringify(to)"><slot /></a>',
        },
        Badge: { template: '<span><slot /></span>' },
      },
    },
  })
}

const headers = (wrapper) => wrapper.findAll('th').map((th) => th.text())
const cells = (wrapper) => wrapper.findAll('td').map((td) => td.text())

describe('RecordsListWidget', () => {
  test('renders a column per field and a row per record', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, {
      widget: { field_ids: [1, 2] },
      results: [
        { id: 1, Name: 'First', Region: 'Riyadh' },
        { id: 2, Name: 'Second', Region: 'Jeddah' },
      ],
    })

    expect(headers(wrapper)).toEqual(['Name', 'Region'])
    expect(cells(wrapper)).toEqual(['First', 'Riyadh', 'Second', 'Jeddah'])
  })

  test('with no fields chosen it shows the first fields of the table', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, {
      results: [{ id: 1, Name: 'First', Region: 'Riyadh', Due: '2026-08-10' }],
    })

    expect(headers(wrapper)).toEqual(['Name', 'Region', 'Due'])
  })

  test('cells render by field type', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, {
      widget: { field_ids: [1, 4, 5] },
      results: [
        {
          id: 1,
          Name: 'First',
          Stage: { id: 9, value: 'Won', color: 'light-green' },
          Amount: '1250000.00',
        },
      ],
    })

    const pill = wrapper.find('.widget-pill')
    expect(pill.text()).toBe('Won')
    expect(pill.classes()).toContain('background-color--light-green')
    expect(wrapper.find('.widget-table__number').text()).toBe('1,250,000.00')
    expect(wrapper.findAll('th')[2].classes()).toContain(
      'widget-table__cell--end'
    )
  })

  test('the header counts the records and links to the table', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, {
      dataSource: { table_id: 12, view_id: 5 },
      results: [{ id: 1, Name: 'First' }],
    })

    expect(wrapper.find('.widget-count').text()).toBe(
      'recordsListWidget.count.one - 1'
    )
    expect(
      JSON.parse(wrapper.find('.stub-link').attributes('data-to'))
    ).toEqual({
      name: 'database-table',
      params: { databaseId: 40, tableId: 12, viewId: 5 },
    })
  })

  test('an empty result set says so instead of rendering an empty table', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, { results: [] })

    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.find('.widget-frame__state').text()).toContain(
      'recordsListWidget.noRecords'
    )
  })

  test('a misconfigured data source says so', async () => {
    const wrapper = await mountListWidget(RecordsListWidget, { error: true })

    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.find('.widget-frame__state').text()).toContain(
      'recordsListWidget.misconfigured'
    )
  })
})

describe('UpcomingDatesWidget', () => {
  const isoDaysFromNow = (days) => {
    const date = new Date()
    date.setDate(date.getDate() + days)
    return date.toISOString().slice(0, 10)
  }

  const mountAgenda = (options = {}) =>
    mountListWidget(UpcomingDatesWidget, {
      dataSource: {
        type: 'local_jadawel_upcoming_rows',
        date_field_id: 3,
        ...(options.dataSource || {}),
      },
      widget: { field_ids: [1, 2], ...(options.widget || {}) },
      results: options.results,
      error: options.error,
    })

  const titles = (wrapper) =>
    wrapper.findAll('.widget-agenda__title').map((title) => title.text())

  test('each row shows its date as a tile, the first field as its title', async () => {
    const wrapper = await mountAgenda({
      widget: { field_ids: [1, 3, 2] },
      results: [
        { id: 1, Name: 'Renewal', Region: 'Riyadh', Due: isoDaysFromNow(3) },
      ],
    })

    // 'Due' is the tile, so it is not repeated among the text even though it
    // was also selected as a displayed field.
    expect(titles(wrapper)).toEqual(['Renewal'])
    expect(wrapper.find('.widget-agenda__details').text()).toBe('Riyadh')
    expect(wrapper.find('.widget-agenda__day').text()).toBe(
      String(Number(isoDaysFromNow(3).slice(8)))
    )
    expect(wrapper.find('.widget-agenda__due').text()).toBe(
      'upcomingDatesWidget.inDays.other - 3'
    )
  })

  test('rows are grouped by how soon they fall due', async () => {
    const wrapper = await mountAgenda({
      results: [
        { id: 1, Name: 'Late', Due: isoDaysFromNow(-2) },
        { id: 2, Name: 'Now', Due: isoDaysFromNow(0) },
        { id: 3, Name: 'Soon', Due: isoDaysFromNow(2) },
        { id: 4, Name: 'Far', Due: isoDaysFromNow(20) },
      ],
    })

    expect(
      wrapper.findAll('.widget-agenda__group-title').map((h) => h.text())
    ).toEqual([
      'upcomingDatesWidget.group.overdue',
      'upcomingDatesWidget.group.today',
      'upcomingDatesWidget.group.week',
      'upcomingDatesWidget.group.later',
    ])
    expect(
      wrapper.find('.widget-agenda__item--today .widget-agenda__due').text()
    ).toBe('upcomingDatesWidget.today')
  })

  test('an overdue row is flagged and counted', async () => {
    const wrapper = await mountAgenda({
      results: [
        { id: 1, Name: 'Late', Region: 'Riyadh', Due: isoDaysFromNow(-2) },
        { id: 2, Name: 'Soon', Region: 'Jeddah', Due: isoDaysFromNow(2) },
      ],
    })

    const items = wrapper.findAll('.widget-agenda__item')
    expect(items[0].classes()).toContain('widget-agenda__item--overdue')
    expect(items[1].classes()).not.toContain('widget-agenda__item--overdue')
    expect(wrapper.find('.widget-status--danger').text()).toContain(
      'upcomingDatesWidget.overdue.one'
    )
  })

  test('a row due today is not flagged as overdue', async () => {
    // The boundary matters: "overdue" means before the start of today, so
    // something due later today is still upcoming.
    const wrapper = await mountAgenda({
      results: [
        { id: 1, Name: 'Today', Region: 'Riyadh', Due: isoDaysFromNow(0) },
      ],
    })

    expect(wrapper.find('.widget-agenda__item').classes()).toContain(
      'widget-agenda__item--today'
    )
    expect(wrapper.find('.widget-status--danger').exists()).toBe(false)
  })

  test('an empty agenda says nothing is due', async () => {
    const wrapper = await mountAgenda({ results: [] })

    expect(wrapper.find('.widget-frame__state').text()).toContain(
      'upcomingDatesWidget.nothingDue'
    )
  })

  test('rows with no date field configured still render', async () => {
    // The data source can be mid-configuration; the widget must not throw.
    const wrapper = await mountAgenda({
      dataSource: { date_field_id: null },
      results: [{ id: 1, Name: 'Renewal', Region: 'Riyadh' }],
    })

    expect(titles(wrapper)).toEqual(['Renewal'])
    expect(wrapper.find('.widget-agenda__day').text()).toBe('—')
  })
})
