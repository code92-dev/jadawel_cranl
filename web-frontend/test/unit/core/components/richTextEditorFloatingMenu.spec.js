import { mount } from '@vue/test-utils'
import { nextTick, ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import RichTextEditorFloatingMenu from '@jadawel/modules/core/components/editor/RichTextEditorFloatingMenu'

const BubbleMenuStub = {
  name: 'BubbleMenu',
  props: ['options'],
  template: '<div><slot /></div>',
}

const editor = {
  isActive: vi.fn(() => false),
}

describe('RichTextEditorFloatingMenu', () => {
  const originalDirection = document.documentElement.dir

  afterEach(() => {
    document.documentElement.dir = originalDirection
  })

  it.each([
    ['ltr', 'left'],
    ['rtl', 'right'],
  ])('places the menu on the correct side in %s', (direction, placement) => {
    document.documentElement.dir = direction

    const wrapper = mount(RichTextEditorFloatingMenu, {
      props: { editor },
      global: {
        mocks: {
          $i18n: { locale: ref(direction === 'rtl' ? 'ar' : 'en') },
          $t: (key) => key,
        },
        stubs: { BubbleMenu: BubbleMenuStub },
      },
    })

    expect(
      wrapper.findComponent(BubbleMenuStub).props('options').placement
    ).toBe(placement)

    wrapper.unmount()
  })

  it('updates the placement when the interface direction changes', async () => {
    const locale = ref('en')
    document.documentElement.dir = 'ltr'

    const wrapper = mount(RichTextEditorFloatingMenu, {
      props: { editor },
      global: {
        mocks: {
          $i18n: { locale },
          $t: (key) => key,
        },
        stubs: { BubbleMenu: BubbleMenuStub },
      },
    })

    expect(
      wrapper.findComponent(BubbleMenuStub).props('options').placement
    ).toBe('left')

    locale.value = 'ar'
    document.documentElement.dir = 'rtl'
    await nextTick()

    expect(
      wrapper.findComponent(BubbleMenuStub).props('options').placement
    ).toBe('right')

    wrapper.unmount()
  })

  it.each([
    ['ltr', 'left', 100],
    ['rtl', 'right', 300],
  ])(
    'anchors the floating menu to the %s editor edge',
    (direction, _, edge) => {
      document.documentElement.dir = direction

      const editorWithView = {
        ...editor,
        view: {
          state: {
            selection: { from: 1 },
            doc: { content: { size: 10 } },
          },
          coordsAtPos: vi.fn(() => ({
            top: 20,
            bottom: 40,
            left: 120,
            right: 120,
          })),
          dom: {
            getBoundingClientRect: () => ({ left: 100, right: 300 }),
          },
        },
      }

      const wrapper = mount(RichTextEditorFloatingMenu, {
        props: { editor: editorWithView },
        global: {
          mocks: {
            $i18n: { locale: ref(direction === 'rtl' ? 'ar' : 'en') },
            $t: (key) => key,
          },
          stubs: { BubbleMenu: BubbleMenuStub },
        },
      })

      expect(wrapper.vm.getVirtualElement().getBoundingClientRect().left).toBe(
        edge
      )

      wrapper.unmount()
    }
  )
})
