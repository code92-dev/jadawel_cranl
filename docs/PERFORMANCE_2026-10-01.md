# Page-load performance after the security release — 2026-10-01

## Question

After `2.3.17-security-audit` was deployed and
`JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=yes` was set in CranL, the app felt
slower. Is the setting the cause, and what actually costs time?

## The setting is not the cause

`JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER` changes three things, none of them on a
hot path:

- Django settings (`base.py`): `SECURE_PROXY_SSL_HEADER`, the `Secure` flag on
  the session and CSRF cookies, and HSTS values. No `SECURE_SSL_REDIRECT`, so no
  extra redirect.
- `docker-entrypoint.sh`: gunicorn gets `--forwarded-allow-ips='*'`, which makes
  uvicorn read `X-Forwarded-For`/`-Proto` per request — one header parse.
- Rate limiting is unaffected: DRF's `get_ident` reads `X-Forwarded-For` with
  `NUM_PROXIES`, which uvicorn leaves in place.

Live response times right after the deploy were normal: `/api/settings/`
120–130 ms and the SSR `/login` 250 ms time-to-first-byte from Germany through
Bunny.

## What the deploy did cost: a one-time cold cache

Every release rebuilds the Nuxt bundle with new content hashes. Each browser
downloads ~2 MB compressed again (the entry chunk alone is 757 KB Brotli,
3.1 MB raw), and each Bunny edge fetches the new files from the Saudi origin on
first request — 28 of the login page's 137 assets were still CDN misses on the
German edge the next morning. This is a one-time cost per browser per release.

## What costs time on every load

Measured with Chromium on `https://app.jadawl.site/login`, three loads in one
browser:

| Load | Response start | DOMContentLoaded | Arabic messages | English messages |
| ---- | -------------: | ---------------: | --------------: | ---------------: |
| Cold | 883 ms | 2,428 ms | 2,573 → 2,956 ms | 2,976 → 3,367 ms |
| Warm | 525 ms | 786 ms | 996 → 1,555 ms | 1,571 → 2,118 ms |
| Warm | 423 ms | 655 ms | 794 → 1,335 ms | 1,351 → 1,905 ms |

1. **Translations: ~1.1 s on every load, cache or not.** The browser fetched
   `/_i18n/<hash>/ar/messages.json` (93 KB) and then, because core's i18n plugin
   awaits the English fallback, `/en/messages.json` (76 KB) — one after the
   other, after DOMContentLoaded, before the app mounts. Both are uncacheable in
   production: CranL's Bunny pull zone rewrites **every JSON response** to
   `Cache-Control: no-cache` and never stores it (the origin sends
   `max-age=86400`; even Nuxt's immutable `/_nuxt/builds/meta/*.json` comes back
   `no-cache`), while `.js`/`.css` keep `public, max-age=31536000, immutable` and
   are CDN hits. This is the limit `REFRESH_PERFORMANCE_2026-09-06.md` ran into.
2. **Logo: 188 KB** for a 29 px tall image (`logo.png`, 1654×548), requested
   twice on the login page (prefetch + `<img>`).

## Changes

- `web-frontend/modules/arabase/i18nBundledMessages.client.js` (additive): the
  client build already contains every locale's messages, precompiled, as hashed
  `/_nuxt/*.js` chunks. @nuxtjs/i18n reads them instead of the JSON route when
  `ctx.dynamicResourcesSSG` is true, and checks that flag on every load. The
  plugin sets it from `i18n:beforeLocaleSwitch`, which fires just before the
  first load. Server rendering still uses the route, answered from Nitro's
  in-process cache. Warm loads now take messages from the browser cache; cold
  loads fetch them from the CDN in parallel.
- `logo.png` resized to 350×116 at 64 colours: 3.6 KB, which Vite inlines into
  the page. Logged in `PATCHES.md`.

## Verification

- Production build of this change served on localhost against the local
  backend, driven by headless Chromium: Arabic (`lang=ar`, `dir=rtl`, «مرحباً
  بعودتك», `$t('action.save')` → «حفظ») and English (`Welcome back`, `Save`)
  both hydrate with **zero `/_i18n/` requests** and a clean console (no
  hydration warnings).
- Vitest: new `test/unit/arabase/i18nBundledMessages.spec.js`, plus
  `productionRuntime` and `publicView` (logo snapshot) — 9 passed.
- Locale parity 4342/4342.

After deploying, re-run the measurement above: the two `messages.json` rows
should be gone and the warm-load mount should move ~1.1 s earlier.

## Not changed

- The 757 KB (Brotli) entry chunk. Splitting it is the next real win for cold
  loads but is a build-structure project, not a fix.
- The English fallback is still loaded for Arabic users. Locale parity makes it
  unnecessary today, but it keeps a missing key showing English instead of a raw
  key path; served from the browser cache it costs a few milliseconds.

## Local test environment note

`web-frontend/node_modules` in the main checkout was installed with pnpm and
mixes Vite 7 and Vite 8, so every Vitest run fails with
`Missing field moduleType`. A `yarn install --frozen-lockfile` (Node 24 at
`/opt/node24/bin`) fixes it; the verification above ran in a clean worktree.
