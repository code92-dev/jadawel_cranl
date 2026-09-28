import { mountSuspended } from '@nuxt/test-utils/runtime'

import DashboardCanvasToolbar from '@jadawel/modules/arabase/dashboard/components/DashboardCanvasToolbar'
import WidgetGalleryModal from '@jadawel/modules/arabase/dashboard/components/WidgetGalleryModal'
import WidgetAppearanceForm from '@jadawel/modules/arabase/dashboard/components/widget/WidgetAppearanceForm'

const dashboard = { id: 1, workspace: { id: 1 } }

describe('WidgetGalleryModal', () => {
  const type = (name, category, variations) => ({
    getType: () => name,
    isAvailable: () => true,
    category,
    defaultSize: { width: 4, height: 4 },
    variations,
  })

  const mountGallery = async () => {
    const types = [
      type('summary', 'numbers', [
        { name: 'Key number', params: {}, size: { width: 3, height: 2 } },
      ]),
      type('chart', 'charts', [
        { name: 'Bar', params: { chart_type: 'bar' }, category: 'charts' },
        { name: 'Line', params: { chart_type: 'line' }, category: 'charts' },
      ]),
      type('text', 'text', [
        { name: 'Section', params: { text_style: 'section' } },
      ]),
    ]
    const wrapper = await mountSuspended(WidgetGalleryModal, {
      props: { dashboard },
      global: {
        mocks: { $registry: { getOrderedList: () => types } },
        stubs: { Modal: { template: '<div><slot /></div>' } },
      },
    })
    wrapper.vm.hide = vi.fn()
    return wrapper
  }

  test('variations are listed under their category', async () => {
    const wrapper = await mountGallery()

    expect(
      wrapper.findAll('.widget-gallery__section-title').map((t) => t.text())
    ).toEqual([
      'widgetGallery.category.numbers',
      'widgetGallery.category.charts',
      'widgetGallery.category.text',
    ])
    expect(wrapper.findAll('.widget-gallery__card')).toHaveLength(4)
  })

  test('choosing one emits it with the size it is created at', async () => {
    const wrapper = await mountGallery()

    await wrapper.findAll('.widget-gallery__card')[1].trigger('click')

    const [variation] = wrapper.emitted('select')[0]
    expect(variation.params).toEqual({ chart_type: 'bar' })
    // No size of its own: the type's default.
    expect(variation.size).toEqual({ width: 4, height: 4 })
    expect(wrapper.vm.hide).toHaveBeenCalled()
  })
})

describe('WidgetAppearanceForm', () => {
  const mountForm = async (appearance = {}, features) => {
    const dispatch = vi.fn().mockResolvedValue()
    const wrapper = await mountSuspended(WidgetAppearanceForm, {
      props: {
        widget: { id: 3, type: 'summary', appearance },
        ...(features ? { features } : {}),
      },
      global: { mocks: { $store: { dispatch } } },
    })
    return { wrapper, dispatch }
  }

  test('a colour change writes the whole appearance', async () => {
    const { wrapper, dispatch } = await mountForm({ icon: 'coins' })

    await wrapper.findAll('.widget-appearance-form__swatch')[1].trigger('click')

    expect(dispatch).toHaveBeenCalledWith('dashboardApplication/updateWidget', {
      widgetId: 3,
      values: { appearance: { icon: 'coins', color: 'blue' } },
      originalValues: { appearance: { icon: 'coins' } },
    })
  })

  test('clearing an option removes it instead of storing null', async () => {
    const { wrapper, dispatch } = await mountForm({
      icon: 'coins',
      color: 'red',
    })

    // The first icon button is "no icon".
    await wrapper.findAll('.widget-appearance-form__icon')[0].trigger('click')

    expect(dispatch.mock.calls[0][1].values).toEqual({
      appearance: { color: 'red' },
    })
  })

  test('only the features a widget uses are offered', async () => {
    const { wrapper } = await mountForm({}, ['color'])

    expect(wrapper.find('.widget-appearance-form__swatches').exists()).toBe(
      true
    )
    expect(wrapper.find('.widget-appearance-form__icons').exists()).toBe(false)
    expect(wrapper.find('.widget-appearance-form__affixes').exists()).toBe(
      false
    )
  })

  test('the current choices are marked', async () => {
    const { wrapper } = await mountForm({ color: 'cyan', icon: 'truck' })

    expect(
      wrapper
        .find('.widget-appearance-form__swatch--active')
        .attributes('aria-label')
    ).toBe('widgetAppearance.colors.cyan')
    expect(
      wrapper.find('.widget-appearance-form__icon--active').attributes('title')
    ).toBe('truck')
  })
})

describe('DashboardCanvasToolbar', () => {
  const mountToolbar = async ({ isEditMode = false, widgets = [] } = {}) => {
    const dispatch = vi.fn().mockResolvedValue()
    const wrapper = await mountSuspended(DashboardCanvasToolbar, {
      props: { dashboard, storePrefix: 'public/', canCreateWidget: true },
      global: {
        mocks: {
          $store: {
            dispatch,
            getters: {
              'public/dashboardApplication/isEditMode': isEditMode,
              'public/dashboardApplication/isEmpty': widgets.length === 0,
              'public/dashboardApplication/getWidgets': widgets,
            },
          },
        },
        stubs: {
          ButtonIcon: {
            emits: ['click'],
            template:
              '<button class="stub-refresh" @click="$emit(\'click\')" />',
          },
          Button: {
            emits: ['click'],
            template: '<button class="stub-add" @click="$emit(\'click\')" />',
          },
        },
      },
    })
    return { wrapper, dispatch }
  }

  test('refresh fetches each data source once', async () => {
    const { wrapper, dispatch } = await mountToolbar({
      widgets: [
        { id: 1, data_source_id: 7 },
        { id: 2, data_source_id: 8 },
        { id: 3, data_source_id: 7 },
        { id: 4 },
      ],
    })

    await wrapper.find('.stub-refresh').trigger('click')

    expect(dispatch.mock.calls.map((call) => call[1])).toEqual([7, 8])
    expect(dispatch.mock.calls[0][0]).toBe(
      'public/dashboardApplication/dispatchDataSource'
    )
    expect(wrapper.find('.dashboard-toolbar__updated').exists()).toBe(true)
  })

  test('editing swaps refresh for adding a widget', async () => {
    const { wrapper } = await mountToolbar({
      isEditMode: true,
      widgets: [{ id: 1 }],
    })

    expect(wrapper.find('.stub-refresh').exists()).toBe(false)
    await wrapper.find('.stub-add').trigger('click')
    expect(wrapper.emitted('add-widget')).toHaveLength(1)
  })
})
