/**
 * Production Nuxt configuration
 *
 * We use a direct import rather than `extends: ['./nuxt.config.base.ts']` because
 * Nuxt 4's `extends` mechanism is designed for Nuxt layers (directories containing
 * their own nuxt.config.ts, app.vue, pages/, etc.), not for importing individual
 * config files directly.
 *
 * When pointing `extends` to a .ts file, Nuxt shows:
 *   "WARN Cannot extend config from ./nuxt.config.base.ts"
 *
 * By using a standard ES module import/export, we achieve the same result reliably.
 */

import baseConfig from './nuxt.config.base.ts'
export default {
  ...baseConfig,
  i18n: {
    ...baseConfig.i18n,
    experimental: {
      ...baseConfig.i18n?.experimental,
      // Translation messages are bundled public assets, with a deployment hash
      // in their URL. Cache them across reloads instead of reloading both locales.
      cacheLifetime: 86400,
      httpCacheDuration: 86400,
    },
  },
  nitro: {
    ...baseConfig.nitro,
    // A single SSR process serializes CPU-heavy document rendering and causes
    // unrelated health requests to queue behind login traffic. The cluster
    // entrypoint lets the runtime use a small, explicitly bounded worker pool.
    preset: 'node-cluster',
  },
  sourcemap: {
    // Server maps stay on: they are never served to a browser and they are what
    // makes a backend stack trace readable.
    server: true,
    // Client maps are emitted but not referenced, so Sentry can still symbolicate
    // an uploaded bundle while the public site does not hand out 4.2 MB of
    // original source to anyone who appends `.map` to a chunk URL.
    client: 'hidden',
  },
  hooks: {
    ...baseConfig.hooks,
    // Nuxt adds a `<link rel="prefetch">` to every page for each chunk a later
    // navigation might need: 53 on top of the ~90 the page itself loads. A
    // hard refresh requests all of them at once, and CranL's edge answers one
    // address with 429 past roughly 100 simultaneous requests, so the hints
    // pushed the page over the limit (docs/DEPLOY_CRANL.md, Troubleshooting).
    // The renderer emits a prefetch link only for manifest entries marked
    // `prefetch`; without it a chunk is fetched when it is first needed, from
    // the edge cache.
    'build:manifest'(manifest) {
      for (const entry of Object.values(manifest)) {
        entry.prefetch = false
      }
    },
  },
  features: {
    // Nuxt inlines every stylesheet into the SSR response by default. That is a
    // good trade for a small stylesheet and a bad one here: the bundle is 1.8 MB
    // (~188 KB gzipped) and it was being re-sent, uncacheable, on every single
    // document request. As an external file it is fetched once and then served
    // from cache under the `immutable` header the rest of `/_nuxt` already uses.
    inlineStyles: false,
  },
}
