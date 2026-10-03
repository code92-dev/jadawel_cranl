import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useNuxtApp, useState } from '#imports'

import { injectNow, provideNow } from '@jadawel/modules/core/composables/useNow'

const Child = defineComponent({
  setup() {
    return { now: injectNow() }
  },
  render() {
    return h('span', String(this.now ?? 'none'))
  },
})

const Page = defineComponent({
  setup() {
    provideNow(1000)
  },
  render() {
    return h(Child)
  },
})

describe('useNow', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-01T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  test('children read one clock that advances on the interval', async () => {
    const wrapper = mount(Page)
    const start = Number(wrapper.text())
    expect(start).toBe(Date.parse('2026-01-01T12:00:00Z'))

    vi.advanceTimersByTime(2500)
    await nextTick()
    expect(Number(wrapper.text())).toBe(start + 2000)

    wrapper.unmount()
    expect(vi.getTimerCount()).toBe(0)
  })

  test('hydrates with the moment the server rendered, then moves on', async () => {
    // Jadawel: an item viewed a few seconds before the server rendered the
    // page must get the same label in the browser while it hydrates.
    const serverRendered = Date.parse('2026-01-01T11:59:56Z')
    useState('jadawel-provided-now').value = serverRendered
    const nuxtApp = useNuxtApp()
    const wasHydrating = nuxtApp.isHydrating
    nuxtApp.isHydrating = true
    try {
      const wrapper = mount(Page)
      expect(Number(wrapper.text())).toBe(serverRendered)

      await nextTick()
      expect(Number(wrapper.text())).toBe(Date.parse('2026-01-01T12:00:00Z'))
      wrapper.unmount()
    } finally {
      nuxtApp.isHydrating = wasHydrating
    }
  })

  test('is null without a providing page', () => {
    expect(mount(Child).text()).toBe('none')
  })
})
