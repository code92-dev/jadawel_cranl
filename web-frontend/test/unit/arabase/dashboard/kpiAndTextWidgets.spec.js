import { mountSuspended } from '@nuxt/test-utils/runtime'

import KpiWidget from '@jadawel/modules/arabase/dashboard/components/widget/KpiWidget'
import TextWidget from '@jadawel/modules/arabase/dashboard/components/widget/TextWidget'

const dashboard = { id: 1, workspace: { id: 1 } }

describe('KpiWidget', () => {
  const mountKpi = async ({
    widget = {},
    result = '1610000.00',
    formatted,
    field = { name: 'Budget' },
  } = {}) => {
    const dataSource = {
      id: 7,
      type: 'local_jadawel_aggregate_rows',
      aggregation_type: 'sum',
      context_data: { field },
    }
    return await mountSuspended(KpiWidget, {
      props: {
        dashboard,
        widget: {
          id: 3,
          type: 'summary',
          title: 'Budget',
          description: '',
          data_source_id: 7,
          ...widget,
        },
      },
      global: {
        mocks: {
          $store: {
            getters: {
              'dashboardApplication/getDataSourceById': () => dataSource,
              'dashboardApplication/getDataForDataSource': () => ({ result }),
              'dashboardApplication/isEditMode': false,
            },
          },
          $registry: {
            exists: () => true,
            get: () => ({
              getName: () => 'Sum',
              getResult: (ds, data) => formatted ?? data.result,
            }),
          },
        },
        stubs: { Badge: { template: '<span><slot /></span>' } },
      },
    })
  }

  const value = (wrapper) => wrapper.find('.widget-kpi__value').text()

  test('a plain number gets thousands separators', async () => {
    expect(value(await mountKpi())).toBe('1,610,000')
  })

  test('the widget chooses compact notation, decimals and a unit', async () => {
    const wrapper = await mountKpi({
      widget: { appearance: { compact: true, suffix: 'SAR', decimals: 2 } },
    })

    expect(value(wrapper)).toBe('1.61M SAR')
  })

  test('a value its field formats itself is kept as it is', async () => {
    const wrapper = await mountKpi({ result: '0.45', formatted: '45%' })

    expect(value(wrapper)).toBe('45%')
  })

  test('with no description, a caption says what is counted', async () => {
    const plain = await mountKpi()
    expect(plain.find('.widget-kpi__caption').text()).toBe('kpiWidget.caption')

    const described = await mountKpi({
      widget: { description: 'All projects' },
    })
    expect(described.find('.widget-kpi__caption').exists()).toBe(false)
  })

  test('an icon and an accent from the appearance', async () => {
    const wrapper = await mountKpi({
      widget: { appearance: { icon: 'coins', color: 'blue' } },
    })

    expect(wrapper.find('.widget-frame__icon i').classes()).toContain(
      'iconoir-coins'
    )
    expect(wrapper.find('.widget-frame').classes()).toContain(
      'widget-accent--blue'
    )
  })

  test('nothing to show yet reads as a dash', async () => {
    const wrapper = await mountKpi({ result: null })

    expect(value(wrapper)).toBe('—')
  })
})

describe('TextWidget', () => {
  const mountText = async (widget = {}, isEditMode = false) =>
    await mountSuspended(TextWidget, {
      props: {
        dashboard,
        widget: {
          id: 4,
          type: 'text',
          title: 'Delivery',
          body: '',
          text_style: 'note',
          ...widget,
        },
      },
      global: {
        mocks: {
          $store: {
            getters: { 'dashboardApplication/isEditMode': isEditMode },
          },
        },
      },
    })

  test('a note shows its title and body, line breaks and all', async () => {
    const wrapper = await mountText({ body: 'One\nTwo' })

    expect(wrapper.find('h3.widget-text__title').text()).toBe('Delivery')
    expect(wrapper.find('.widget-text__body').element.textContent.trim()).toBe(
      'One\nTwo'
    )
  })

  test('the body is text, never markup', async () => {
    const wrapper = await mountText({ body: '<img src=x onerror=alert(1)>' })

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.widget-text__body').text()).toContain('<img')
  })

  test('a section is a heading; a callout gets an accent and an icon', async () => {
    const section = await mountText({ text_style: 'section' })
    expect(section.find('h2.widget-text__title').exists()).toBe(true)
    expect(section.classes()).toContain('widget-text--section')

    const callout = await mountText({ text_style: 'callout' })
    expect(callout.classes()).toContain('widget-accent--blue')
    expect(callout.find('.widget-text__icon i').classes()).toContain(
      'iconoir-light-bulb'
    )
  })

  test('an empty body invites an editor to write one', async () => {
    const reading = await mountText()
    expect(reading.find('.widget-text__placeholder').exists()).toBe(false)

    const editing = await mountText({}, true)
    expect(editing.find('.widget-text__placeholder').exists()).toBe(true)
  })

  test('the title is the drag handle', async () => {
    const wrapper = await mountText()

    expect(wrapper.find('.widget-text__title.widget__header').exists()).toBe(
      true
    )
  })
})
