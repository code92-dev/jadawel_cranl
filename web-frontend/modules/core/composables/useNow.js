import { inject, onBeforeUnmount, onMounted, provide, ref } from 'vue'
import { useNuxtApp, useState } from '#imports'

export const nowKey = Symbol('now')

/**
 * A timestamp that keeps ticking while the page is open, so relative dates
 * computed from it keep ageing instead of freezing at the moment they were
 * rendered. One page provides it and every card reads the same value, so a
 * long list costs a single timer.
 *
 * Jadawel: the server's moment is carried to the browser in the payload and
 * used while the page hydrates. Taking `Date.now()` on both sides made an item
 * viewed four seconds before the server rendered it "just now" there and "less
 * than a minute ago" in the browser a second later: a hydration mismatch. Once
 * mounted, the clock moves on to the real time.
 *
 * @param {number} intervalMs How often the value advances.
 * @returns {import('vue').Ref<number>} The current time in milliseconds.
 */
export function provideNow(intervalMs = 60 * 1000) {
  const nuxtApp = useNuxtApp()
  const rendered = useState('jadawel-provided-now', () => Date.now())
  const now = ref(
    import.meta.server || nuxtApp.isHydrating ? rendered.value : Date.now()
  )
  let timer = null
  onMounted(() => {
    now.value = Date.now()
    timer = setInterval(() => {
      now.value = Date.now()
    }, intervalMs)
  })
  onBeforeUnmount(() => clearInterval(timer))
  provide(nowKey, now)
  return now
}

/**
 * @returns {import('vue').Ref<number>|null} The provided clock, or `null`
 *   outside of a page that provides one.
 */
export function injectNow() {
  return inject(nowKey, null)
}
