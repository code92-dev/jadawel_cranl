# Refresh performance review — 2026-09-06

## Scope and findings

Measured the public login page at `https://app.jadawl.site/login` with Chromium,
using an initial navigation followed by another navigation in the same browser
context. The root domain now serves the marketing site, so its timings were
excluded. These are individual observations from this machine, not percentile
benchmarks or measurements of an authenticated table.

| Observed metric | Initial navigation | Warm navigation |
| --- | ---: | ---: |
| Document response start | 1,907 ms | 1,048 ms |
| DOM content loaded | 2,601 ms | 1,109 ms |
| Arabic messages request | 1,101 ms | 1,273 ms |
| English messages request | 802 ms | 860 ms |

The translation requests occur during client initialization and can finish after
DOM content loaded. Their durations must not be added to each other or interpreted
as the entire refresh time. The warm navigation still transferred approximately
145 KB across the two translation responses. A separate header check confirmed
`Cache-Control: no-cache` and a CDN miss on the Arabic messages endpoint.

The largest observed JavaScript resource transferred approximately 1.36 MB on the
initial navigation, but was cached on the warm navigation. Server response time
also remains a material part of reload latency.

## Changes

- Production i18n now explicitly enables a 24-hour message cache and a 24-hour HTTP
  cache. Messages are bundled public translations; their URL contains a build-specific
  hash. Authenticated HTML and application/API data receive no new caching rules.
  Development configuration stays unchanged.
- Workspace loading/selection and application loading now start concurrently.
  Previously the application request started only after workspace fetching and
  permission loading completed. Navigation still awaits both branches.
- Regression coverage checks request overlap, permission completion, application
  errors, loaded-list reuse, and signed-out behavior.

The cache settings are supported by the installed Nuxt i18n implementation;
[Nuxt i18n documentation](https://i18n.nuxtjs.org/docs/api/options#httpcacheduration)
also describes the HTTP cache duration setting.

## Verification

The overlap test failed against the original middleware (`expected false to be
true`) and passed after the change. All 20 focused tests passed:

```bash
cd web-frontend
APP_ENV=test ./node_modules/.bin/vitest --run \
  test/unit/core/middleware/workspacesAndApplications.spec.js \
  test/unit/config/productionRuntime.spec.js \
  test/unit/core/store/workspace.spec.js
```

Targeted ESLint passed. Arabic locale parity passed: 3,763/3,763 keys, zero missing.

The full production build passed with the repository's standard 8 GB Node heap
limit (a preliminary 4 GB build exhausted its heap). Build output was isolated
under `/tmp/jadawel-perf-output`, leaving existing local services untouched.

The built server returned `Cache-Control: max-age=86400` for locale messages.
Chromium loaded Arabic and English correctly (`lang=ar`, `dir=rtl`, Arabic login
title), with no page errors. On both a second navigation and an explicit browser reload, translation resources
reported **zero transferred bytes**, versus about 145 KB compressed on the live
warm-navigation baseline. The local server serves uncompressed data directly, so
first-load byte sizes cannot be compared to the live CDN's compressed responses.
Local timings are not comparable to production network timings.

## Release status and limits

Changes are local and have not been committed, pushed, or deployed. Production
still needs the published-image/pin/redeploy procedure in `DEPLOY_CRANL.md`,
followed by the same browser check on the deployed app. Do not treat a local cache
check as a measured production speedup.

Authenticated table refresh, row updates, and large-workspace API timings were not
measured without a specific affected page/session. Those remain separate profiling
work if the reported delay persists after these startup fixes.
