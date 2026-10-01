/**
 * Loads translations in the browser from the build's own JS chunks instead of
 * the `/_i18n/<hash>/<locale>/messages.json` server route.
 *
 * In SSR mode @nuxtjs/i18n has the browser fetch every locale it needs from
 * that JSON route on each page load. CranL's CDN rewrites every JSON response
 * to `Cache-Control: no-cache` and never stores it, so each load or refresh
 * re-downloaded ~170 KB and waited on two back-to-back origin round trips —
 * Arabic, then the English fallback core's i18n plugin awaits. Measured on
 * app.jadawl.site with a warm browser cache, that was ~1.1 s after
 * DOMContentLoaded before the app could mount.
 *
 * The client bundle already contains the same messages, precompiled, as
 * content-hashed `/_nuxt/*.js` chunks that are served `immutable` and cached by
 * both the CDN and the browser. The module only reads from them when
 * `ctx.dynamicResourcesSSG` is true, a flag it checks on every load rather than
 * once, so setting it before the first load switches the source with no patch
 * to the module. `i18n:beforeLocaleSwitch` fires immediately before that first
 * load (and before every later one). Server rendering is untouched: it keeps
 * using the route, which Nitro answers from its in-process cache.
 */
export default defineNuxtPlugin({
  name: 'arabase:i18n-bundled-messages',
  // Only registers a hook, so it can run before i18n's own plugins create the
  // context the hook later touches.
  enforce: 'pre',
  setup(nuxtApp) {
    nuxtApp.hook('i18n:beforeLocaleSwitch', () => {
      if (nuxtApp._nuxtI18n) {
        nuxtApp._nuxtI18n.dynamicResourcesSSG = true
      }
    })
  },
})
