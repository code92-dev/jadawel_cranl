import { defineComponent, h } from 'vue'

import Highlight from '@jadawel/modules/core/components/Highlight'
import { TestApp } from '@jadawel/test/helpers/testApp'

// jsdom/happy-dom have no layout engine, so every rect is zeroed. That is
// enough here: Highlight only reads `top`/`left`/`width`/`height`, so the
// assertions stay deterministic.
vi.stubGlobal(
  'ResizeObserver',
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
)

const createHost = () =>
  defineComponent({
    name: 'HighlightHost',
    render() {
      return h('div', { class: 'host' }, [
        h('div', { 'data-highlight': 'target', class: 'target' }),
        h(Highlight, { ref: 'highlight' }),
      ])
    },
  })

describe('Highlight component', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('positions the box around matching elements', async () => {
    const wrapper = await testApp.mount(createHost())
    await wrapper.vm.$refs.highlight.show("[data-highlight='target']")

    const box = wrapper.find('.highlight')
    expect(box.exists()).toBe(true)
    // padding 2 around a zeroed rect: -2px offset, 4px size.
    expect(box.attributes('style')).toContain('top: -2px')
    expect(box.attributes('style')).toContain('left: -2px')
    expect(box.attributes('style')).toContain('width: 4px')
    expect(box.attributes('style')).toContain('height: 4px')
  })

  test('falls back to centered when the selector matches nothing', async () => {
    const wrapper = await testApp.mount(createHost())
    // Must not throw (`Cannot read properties of null (reading 'top')`
    // when getCombinedBoundingClientRect gets an empty list).
    await wrapper.vm.$refs.highlight.show("[data-highlight='gone']")

    const box = wrapper.find('.highlight')
    expect(box.exists()).toBe(true)
    expect(box.attributes('style')).toContain('top: 50%')
    expect(box.attributes('style')).toContain('left: 50%')
  })
})
