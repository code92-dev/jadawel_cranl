import { mountSuspended } from '@nuxt/test-utils/runtime'

import WidgetContext from '@jadawel/modules/dashboard/components/widget/WidgetContext'
import WidgetSizeContext from '@jadawel/modules/arabase/dashboard/components/widget/WidgetSizeContext'
import Context from '@jadawel/modules/core/components/Context'

const dashboard = { id: 1, workspace: { id: 1 } }

describe('WidgetContext size menu item', () => {
  const mountContext = async (hasPermission) => {
    const wrapper = await mountSuspended(WidgetContext, {
      props: { dashboard, widget: { id: 3, title: 'Sales' } },
      global: {
        mocks: {
          $store: { dispatch: vi.fn().mockResolvedValue() },
          $hasPermission: () => hasPermission,
        },
      },
    })
    // Context only renders its slot once it has been opened.
    await wrapper
      .findComponent(Context)
      .setData({ openedOnce: true, open: true })
    return wrapper
  }

  test('the size item is hidden without update permission', async () => {
    const wrapper = await mountContext(false)

    expect(wrapper.text()).not.toContain('widgetContext.size')
    expect(wrapper.findComponent(WidgetSizeContext).exists()).toBe(false)
  })

  test('the size item is visible with update permission', async () => {
    const wrapper = await mountContext(true)

    expect(wrapper.text()).toContain('widgetContext.size')
    expect(wrapper.findComponent(WidgetSizeContext).exists()).toBe(true)
  })
})

describe('WidgetSizeContext', () => {
  const mountPicker = async (
    widget = {},
    minSize = { width: 2, height: 2 }
  ) => {
    const dispatch = vi.fn().mockResolvedValue()
    const wrapper = await mountSuspended(WidgetSizeContext, {
      props: {
        dashboard,
        widget: {
          id: 3,
          type: 'summary',
          title: 'Sales',
          width: 3,
          height: 2,
          ...widget,
        },
      },
      global: {
        mocks: {
          $store: { dispatch },
          $registry: { get: () => ({ minSize }) },
        },
      },
    })
    // Context only renders its slot once it has been opened.
    await wrapper
      .findComponent(Context)
      .setData({ openedOnce: true, open: true })
    return { wrapper, dispatch }
  }

  const widths = (wrapper) => wrapper.findAll('.widget-size-context__option')
  const heights = (wrapper) => wrapper.findAll('.widget-size-context__height')

  test('offers the common widths and heights, marking the current ones', async () => {
    const { wrapper } = await mountPicker()

    expect(widths(wrapper).map((w) => w.text())).toEqual([
      'widgetSize.widths.3',
      'widgetSize.widths.4',
      'widgetSize.widths.6',
      'widgetSize.widths.8',
      'widgetSize.widths.12',
    ])
    expect(heights(wrapper).map((h) => h.text())).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '8',
    ])
    expect(wrapper.find('.widget-size-context__option--active').text()).toBe(
      'widgetSize.widths.3'
    )
    expect(wrapper.find('.widget-size-context__height--active').text()).toBe(
      '2'
    )
  })

  test('choosing a width keeps the height and patches through updateWidget', async () => {
    const { wrapper, dispatch } = await mountPicker()

    await widths(wrapper)[2].trigger('click')

    expect(dispatch).toHaveBeenCalledWith('dashboardApplication/updateWidget', {
      widgetId: 3,
      values: { width: 6, height: 2 },
      originalValues: { width: 3, height: 2 },
    })
    expect(wrapper.emitted('selected')).toHaveLength(1)
  })

  test('choosing a height keeps the width', async () => {
    const { wrapper, dispatch } = await mountPicker()

    await heights(wrapper)[3].trigger('click')

    expect(dispatch.mock.calls[0][1].values).toEqual({ width: 3, height: 4 })
  })

  test('choosing the current size sends nothing', async () => {
    const { wrapper, dispatch } = await mountPicker()

    await heights(wrapper)[1].trigger('click')

    expect(dispatch).not.toHaveBeenCalled()
  })

  test('sizes below the widget type minimum are disabled', async () => {
    const { wrapper } = await mountPicker({}, { width: 4, height: 3 })

    expect(widths(wrapper)[0].attributes('disabled')).toBeDefined()
    expect(widths(wrapper)[1].attributes('disabled')).toBeUndefined()
    expect(heights(wrapper)[1].attributes('disabled')).toBeDefined()
    expect(heights(wrapper)[2].attributes('disabled')).toBeUndefined()
  })

  test('a widget without a size is read as the full-width default', async () => {
    const { wrapper } = await mountPicker({ width: null, height: null })

    expect(wrapper.find('.widget-size-context__option--active').text()).toBe(
      'widgetSize.widths.12'
    )
    expect(wrapper.find('.widget-size-context__height--active').text()).toBe(
      '4'
    )
  })
})
