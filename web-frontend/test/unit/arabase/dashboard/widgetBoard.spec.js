import { mountSuspended } from '@nuxt/test-utils/runtime'

import WidgetBoard from '@jadawel/modules/dashboard/components/WidgetBoard'

const dashboard = { id: 1, workspace: { id: 1 } }

const ChromeStub = {
  name: 'WidgetEditChrome',
  emits: ['preview'],
  template:
    '<button class="chrome-stub" @click="$emit(\'preview\', { width: 9, height: 5 })" />',
}

const mountBoard = async (
  widgets,
  {
    isEditMode = false,
    hasPermission = false,
    canCreateWidget = false,
    minSize,
  } = {}
) => {
  const store = {
    getters: {
      'dashboardApplication/getWidgets': widgets,
      'dashboardApplication/isEditMode': isEditMode,
      'dashboardApplication/getSelectedWidgetId': null,
      'dashboardApplication/getData': {},
    },
    dispatch: vi.fn().mockResolvedValue(),
  }
  // The widget component itself is irrelevant here; the board test only cares
  // about the frame's grid spans. The header div exists because the globally
  // registered v-grid-sortable directive uses it as the drag handle.
  const widgetType = {
    name: 'Stub',
    minSize,
    isLoading: () => false,
    component: {
      template:
        '<div><div class="widget__header"></div><div class="widget-stub"></div></div>',
    },
  }

  return await mountSuspended(WidgetBoard, {
    props: { dashboard, canCreateWidget },
    global: {
      stubs: { WidgetEditChrome: ChromeStub },
      mocks: {
        $store: store,
        $registry: { get: () => widgetType },
        $hasPermission: () => hasPermission,
      },
      directives: { gridSortable: {} },
    },
  })
}

describe('WidgetBoard grid layout', () => {
  test('renders each widget with span styles matching its width/height', async () => {
    const wrapper = await mountBoard([
      { id: 1, type: 'stub', order: '1', width: 6, height: 4 },
      { id: 2, type: 'stub', order: '2', width: 3, height: 1 },
    ])

    const frames = wrapper.findAll('.dashboard-widget')
    expect(frames).toHaveLength(2)
    expect(frames[0].attributes('style')).toContain('grid-column: span 6')
    expect(frames[0].attributes('style')).toContain('grid-row: span 4')
    expect(frames[1].attributes('style')).toContain('grid-column: span 3')
    expect(frames[1].attributes('style')).toContain('grid-row: span 1')
  })

  test('a widget without width/height spans the full row, 4 rows high', async () => {
    const wrapper = await mountBoard([{ id: 1, type: 'stub', order: '1' }])

    const frame = wrapper.find('.dashboard-widget')
    expect(frame.attributes('style')).toContain('grid-column: span 12')
    expect(frame.attributes('style')).toContain('grid-row: span 4')
  })

  test('a size below the widget type minimum is drawn at the minimum', async () => {
    const wrapper = await mountBoard(
      [{ id: 1, type: 'stub', order: '1', width: 1, height: 1 }],
      { minSize: { width: 3, height: 2 } }
    )

    const style = wrapper.find('.dashboard-widget').attributes('style')
    expect(style).toContain('grid-column: span 3')
    expect(style).toContain('grid-row: span 2')
  })

  test('the edit chrome previews a resize on the widget', async () => {
    const wrapper = await mountBoard(
      [
        {
          id: 1,
          type: 'stub',
          order: '1',
          width: 3,
          height: 2,
          dashboard_id: 1,
        },
      ],
      { isEditMode: true, hasPermission: true }
    )

    await wrapper.find('.chrome-stub').trigger('click')

    const frame = wrapper.find('.dashboard-widget')
    expect(frame.attributes('style')).toContain('grid-column: span 9')
    expect(frame.classes()).toContain('dashboard-widget--resizing')
  })

  test('a widget still being created gets no edit chrome', async () => {
    const wrapper = await mountBoard(
      [{ id: 1, type: 'stub', order: '1', width: 3, height: 2 }],
      { isEditMode: true, hasPermission: true }
    )

    expect(wrapper.find('.chrome-stub').exists()).toBe(false)
  })

  test('the add tile shows while editing and asks for the gallery', async () => {
    const reading = await mountBoard([{ id: 1, type: 'stub', order: '1' }], {
      canCreateWidget: true,
    })
    expect(reading.find('.widget-board__add').exists()).toBe(false)

    const editing = await mountBoard([{ id: 1, type: 'stub', order: '1' }], {
      isEditMode: true,
      hasPermission: true,
      canCreateWidget: true,
    })
    await editing.find('.widget-board__add').trigger('click')
    expect(editing.emitted('add-widget')).toHaveLength(1)
  })

  test('drag is offered in edit mode with update permission', async () => {
    const wrapper = await mountBoard(
      [{ id: 1, type: 'stub', order: '1', width: 3, height: 2 }],
      { isEditMode: true, hasPermission: true }
    )

    expect(wrapper.find('.widget-board').classes()).toContain(
      'widget-board--draggable'
    )
  })

  test('drag is disabled below the grid breakpoint', async () => {
    const originalWidth = window.innerWidth
    window.innerWidth = 500
    try {
      const wrapper = await mountBoard(
        [{ id: 1, type: 'stub', order: '1', width: 3, height: 2 }],
        { isEditMode: true, hasPermission: true }
      )

      expect(wrapper.find('.widget-board').classes()).not.toContain(
        'widget-board--draggable'
      )
    } finally {
      window.innerWidth = originalWidth
    }
  })
})
