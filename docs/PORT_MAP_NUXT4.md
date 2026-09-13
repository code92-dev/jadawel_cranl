# PORT_MAP_NUXT4.md

Deliverable: map the Nuxt 3 → Nuxt 4 migration for the Jadawel fork from a three-way diff
(`/tmp/up/x/baserow-2.2.2` → `/tmp/up/x/baserow-2.3.3` → fork). Read-only investigation;
no installs, tests or builds were run. Every claim below is anchored to a path:line I read.

Headline: the Nuxt-4 portion of the 2.3 delta is **small and separable** from the feature
deps. Nuxt-4-relevant = 5 dependency lines + 4 `resolutions` pins + 4 config files +
3 module.js lines. Everything else in the 2.3 package diff is an unrelated feature dep.

---

## Dependency groups

### A. Nuxt-related (this is the migration)

| Package | 2.2.2 | 2.3.3 | Fork today | Note |
|---|---|---|---|---|
| `nuxt` | `^3.21.2` | `^4.4.2` (lock: 4.4.8) | `3.21.10` exact | **the migration** |
| `@nuxt/test-utils` | `^3.21.0` | `^4.0.2` (lock: 4.0.3) | `^3.21.0` | v4 requires `vitest ^4.0.2` + `happy-dom >=20.0.11` |
| `@nuxt/eslint` | `^1.12.1` | `^1.15.2` (lock: 1.16.0) | `^1.12.1` | 1.16 depends on `@nuxt/kit ^4.4.8`; still generates `.nuxt/eslint.config.mjs` |
| `@nuxtjs/storybook` | `latest` | `npm:@nuxtjs/storybook@nightly` (9.1.0-29411911.f34c865) | `9.0.1` | **hard blocker**: 9.0.1 peers `nuxt ^3.13.0` + `storybook ~9.0.5` |
| `storybook` | `^9.1.19` | `10.3.5` | `^9.1.19` | follows the nightly module (peer `storybook ~10.0.2`) |
| `@storybook/addon-docs` | `^9.1.16` | `10.3.5` | `^9.1.16` | storybook 10 line |
| `@storybook/addon-links` | `^9.1.16` | `10.3.5` | `^9.1.16` | storybook 10 line |
| `@vitest/coverage-istanbul` | `^4.0.17` | `4.1.9` | `^4.0.17` | ship with the tested vitest |
| `@vitest/coverage-v8` | `^4.0.17` | `4.1.9` | `^4.0.17` | same |
| `vitest` | `^4.0.17` | `4.1.9` | `^4.0.17` | 3.x would not satisfy test-utils 4 |
| `globals` | `^17.0.0` | `^17.7.0` | `^17.0.0` | transitive of the eslint bump |
| `@sentry/nuxt` | `10.46.0` | `10.47.0` | `10.46.0` | **not required**: installed 10.46.0 already peers `nuxt: ">=3.7.0 || 4.x || 5.x"` |
| `@sentry/vue`, `@sentry/node` | `10.46.0`, `10.47.0` | `10.47.0`, `10.47.0` | `10.46.0`, `10.47.0` | version-alignment only |

`resolutions` added by 2.3.3 (both trees already share `cipher-base`, `unset-value`,
`vuejs3-datepicker/**/minimatch`, `lodash`):

```json
"**/@nuxt/vite-builder/vite": "7.3.6",
"**/vite-node/vite": "7.3.6",
"**/vitest/vite": "8.0.16",
"lru-cache": "8.0.5"
```

Fork lock today resolves `vite` three ways (`7.3.6` top-level, `8.2.2` for the
`^6||^7||^8` range). These pins collapse that; add them with the upgrade.

### B. Unrelated 2.3 feature deps — do NOT port with Nuxt 4

| Package | 2.2.2 → 2.3.3 | Why it is here |
|---|---|---|
| `xlsx` | **added** `https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz` | Excel import (`modules/database/utils/excel.js` ↔ `TableExcelImporter.vue`). Also a non-registry URL — supply-chain review needed. Fork has no xlsx and no Excel importer. |
| `axios` | `1.15.0` → `1.18.0` | feature bump (fork already on `1.18.0`) |
| `form-data` | `4.0.4` → `4.0.6` | (fork already `4.0.6`) |
| `markdown-it` | `14.1.1` → `14.2.0` | (fork already `14.2.0`) |
| `papaparse` | `5.4.1` → `5.5.4` | (fork still `5.4.1`) |
| `tldjs` | `^2.3.1` → `^2.3.2` | (fork still `^2.3.1`) |
| `@zip.js/zip.js` | `^2.8.14` → `^2.8.26` | (fork still `^2.8.14`) |
| `posthog-js` | `^1.232.4` | fork pins `^1.422.5` — fork divergence |
| `prettier:fix` script | loses `--log-level=warn` | cosmetic; fork has its own scripts anyway |

Fork divergences to preserve across the upgrade: `vue-router` `^5.3.0` (upstream 2.3.3
declares `^4.6.3`), `posthog-js ^1.422.5`, `@tiptap/extension-gapcursor ^3.30.5`,
`stylelint-use-logical`, the `version` bump none, `name: jadawel`, and the fork-only
scripts (`scripts/patch-datepicker-locale.mjs` in `postinstall`, `locale:check`,
`locale:check:baseline`, single-config `test`).

---

## Config diffs

### `nuxt.config.ts` — no change
Byte-identical in all three trees (the `isTest/isDev` dispatcher into `config/nuxt.config.{test,dev,prod}.ts`).

### `config/nuxt.config.base.ts` — the only config file with real Nuxt-4 edits

2.3.3 adds, relative to 2.2.2:

```diff
-export default defineNuxtConfig({
-  compatibilityDate: '2025-07-15',
+const frontendCookiePrefix =
+  process.env.BASEROW_FRONTEND_COOKIE_PREFIX ||
+  process.env.NUXT_PUBLIC_BASEROW_FRONTEND_COOKIE_PREFIX ||
+  ''
+
+export default defineNuxtConfig({
+  compatibilityDate: '2025-11-15',
+  // Nuxt 4 defaults to srcDir "app/"; keep v3-style layout (app.vue and modules at project root).
+  srcDir: '.',
   alias: {
     '@baserow': '',
   },
```
```diff
-      cookieKey: 'i18n-language',
+      cookieKey: `${frontendCookiePrefix}i18n-language`,
```
plus a large `vite.optimizeDeps.include` expansion (adds `vuex`, `vuejs3-datepicker`,
`posthog-js`, `@sentry/core`, `@tiptap/pm/transform`, `lodash/isObject`, `xlsx`, …).
`experimental.appManifest`, `build.transpile/cache/cacheDirectory`, `vue.compilerOptions.comments`
and `nitro.externals` are unchanged between 2.2.2 and 2.3.3 — i.e. upstream kept them under Nuxt 4.

Fork-specific content that must survive the merge: `pages: true` (L50), `alias: {'@jadawel': ''}`
(L51-53), `defaultLocale: process.env.NUXT_DEFAULT_LOCALE || 'ar'`, `langDir: '../locales'`
(L72) with its PATCHES.md rationale, the arabase module entry, and the removal of
`premiumBase`/`enterpriseBase`.

Fork currently omits `srcDir`. Nuxt 4's resolver (`@nuxt/schema@4.4.8`
`src/config/common.ts`, `srcDir.$resolve`) returns `rootDir` when `web-frontend/app/` does
not exist, which is the fork's case (no `app/` dir; `app.vue`/`error.vue` at root). So
auto-detection yields `web-frontend/` either way. **Still copy upstream's `srcDir: '.'`** —
it is one line and makes the layout explicit rather than dependent on the heuristic.

### `tsconfig.json` — replace wholesale (upstream migration is optional but recommended)

```diff
-{
-  // https://nuxt.com/docs/guide/concepts/typescript
-  "extends": "./.nuxt/tsconfig.json"
-}
+{
+  // Nuxt 4: project references (see https://nuxt.com/docs/4.x/getting-started/upgrade)
+  "files": [],
+  "references": [
+    { "path": "./.nuxt/tsconfig.app.json" },
+    { "path": "./.nuxt/tsconfig.server.json" },
+    { "path": "./.nuxt/tsconfig.shared.json" },
+    { "path": "./.nuxt/tsconfig.node.json" }
+  ]
+}
```
Nuxt 4 emits four split configs; the current fork `.nuxt/` only has `tsconfig.json` and
`tsconfig.server.json`. The fork has no `typecheck` script, so the required companion change
(`vue-tsc -b --noEmit`) does not apply.

### `server/tsconfig.json` — upstream left it; the guide says delete it
All three trees contain `{"extends":"../.nuxt/tsconfig.server.json"}` and 2.3.3 **did not**
remove it. It is redundant (not harmful) once project references are adopted. The fork's
`server/routes/_health.get.ts` is fork-only and must stay (it is what the Docker
`HEALTHCHECK ... /_health/` and the Helm liveness probe hit).

### `vitest.config.base.ts` — 2.3.3 adds three things

```diff
     pool: 'forks',
+    // Coverage instrumentation with Nuxt can make initial mounts exceed Vitest's
+    // 5s per-test default on CI.
+    testTimeout: 30_000,
+    // setupNuxt() runs in a beforeAll; 10s default hookTimeout is often exceeded (flaky CI / local).
+    hookTimeout: 120_000,
     exclude: [
       ...
       '**/playwright-report/**',
+      // Legacy Nuxt 2-style server tests (create-nuxt); skipped and incompatible with Vitest+Nuxt 4 resolution
+      '**/test/server/**',
     ],
```
`vitest.config.ts`, `vitest.setup.ts`, `stylelint.config.mjs`, `.prettierignore`,
`.stylelintignore`, `jest.config.js`, `i18n.config.ts`, `coverage.config.js` and
`config/nuxt.config.{dev,test,prod}.ts` are identical between 2.2.2 and 2.3.3 apart from the
fork's own edits (prod extras: `node-cluster` preset, i18n cache lifetime, `inlineStyles: false`,
hidden client maps; `eslint.config.mjs`: no premium/enterprise globs, conditional plugin override).

### `eslint.config.mjs` — no Nuxt-4 edit
The `withNuxt` import resolves to `./web-frontend/.nuxt/eslint.config.mjs`, and the fork's
installed `@nuxt/eslint` still uses `join(buildDir, "eslint.config.mjs")` as the default
`configFile`; 1.16.0 keeps that. Only the version bump matters.

### `web-frontend/.storybook/main.ts` — 2.3.3 adds a `viteFinal` `optimizeDeps` block
(`holdUntilCrawlEnd`, pretrained deps) to stop cold-start 504s. Needed only if storybook is kept
on the nightlies.

### `web-frontend/Dockerfile` — bump the base image
`node:24.14.0-trixie-slim` → `24.18.0-trixie-slim` (upstream). Nuxt 4.4.8 declares
`engines.node: ^22.12.0 || ^24.11.0 || >=26.0.0`, so the fork's 24.14.0 already satisfies it;
the bump is maintenance, not a blocker. `.nvmrc` (`24`) and CI (`node-version: "24"`) are fine.
Fork must keep its `scripts/patch-datepicker-locale.mjs` `postinstall` step, which upstream
does not have.

### `modules/*/module.js` — three Nuxt-4 edits

| Fork file | Fork line | Change |
|---|---|---|
| `modules/core/module.js` | 28-32 | **delete** `compatibility: { nuxt: '^3.0.0' }` |
| `modules/builder/module.js` | 16-18 | **delete** the block |
| `modules/dashboard/module.js` | 41-43 | **delete** the block |

2.3.3 has no `compatibility:` meta anywhere in `web-frontend/` (grep for `nuxt: '^[0-9]`
returns nothing; the only `compatibility` hit is a comment at `core/module.js:49`). Under
Nuxt 4 `@nuxt/kit` runs `checkNuxtCompatibility` and, on failure, logs
`Module \`…\` is disabled due to incompatibility issues` and **returns without calling
`setup()`** (throws only when `experimental.enforceModuleCompatibility` is on). A disabled
`core` module means no alias, no plugins, no layouts, no middleware — a dead app.

Otherwise no Nuxt-4-specific module.js changes: `nuxt/kit` vs `@nuxt/kit` (`core` uses the
latter) both resolve in Nuxt 4 (`"./kit": "./kit.js"` → `export * from '@nuxt/kit'`), all
helpers used (`defineNuxtModule, addPlugin, extendPages, addLayout, addRouteMiddleware,
createResolver, addTemplate`) are still exported by `@nuxt/kit@4.4.8`, and the automation
module's added `addRouteMiddleware` in 2.3.3 is a feature change (new
`middleware/selectWorkspaceAutomationWorkflow.js`), not Nuxt 4.

---

## Nuxt 3 APIs to audit

The list below is what the fork **actually uses** (greps over `web-frontend/`, gitignore
honoured), the Nuxt 4 status, and the verdict.

| API / surface | Fork usage (evidence) | Nuxt 4 status | Action |
|---|---|---|---|
| `useAsyncData` | ~22 files, e.g. `modules/core/pages/settings.vue:45`, `modules/database/pages/APIDocsDatabase.vue:208`, `modules/builder/pages/publicPage.vue:56` | kept; behaviour changed | See rows below |
| ↳ key as function/ref | ``useAsyncData(() => `page-editor-${...}`, …)`` `builder/pages/pageEditor.vue:45` | v4 adds reactive-key support | none |
| ↳ destructured `pending` | `builder/pages/pageEditor.vue:3` `v-if="!pending"`, `builder/pages/publicPage.vue:3` `v-if="!pending && !error"` | `pending` is now `status==='pending'` (`pendingWhenIdle` defaults **false**) | awaited (immediate) fetches, so `pending` still flips true→false; low risk. If a loading UI ever looked wrong, use `status === 'success'` |
| ↳ destructured `status/refresh/clear/execute` | `modules/database/pages/APIDocsDatabase.vue:208` | all still returned | none |
| ↳ `dedupe`, `getCachedData`, `transform`, `pick`, `default`, `deep`, `server`, `lazy`, `immediate` options | **none found** | options changed/removed | none — nothing to migrate |
| ↳ shared explicit keys | `'workspace'`, `'verify-email'`, `'health'`, `'instance-id'` (`core/pages/settings.vue:45`, `verifyEmailAddress.vue:40`, `admin/health.vue:86`, `admin/settings.vue:304`) | same-key calls now share refs and warn on conflicting options | keys are page-unique; no conflict |
| `useState` | `arabase/pages/publicDashboard.vue:40`, `publicPageView.vue:59`, `arabase/pages/publicDashboardLogin.vue:67`, `builder/composables/useCollectionElement.js:31` | kept; `clearNuxtState` reset semantics change only at `compatibilityVersion: 5` | none |
| `useHead` / `useHead(() => …)` | `arabase/plugin.js:45`, `core/pages/form.vue:231`, `database/pages/publicView.vue:161`, `builder/components/PublicPageContent.vue:201` | Unhead **v2** | see next three rows |
| ↳ `hid: true` (removed prop) | `modules/core/head.js:22,29,36,43`; `modules/builder/components/PublicPageContent.vue:141` | **removed** | port upstream's fix: named `key:` values + the new `modules/builder/utils/favicon.js` helper |
| ↳ `style: [{ children: … }]` (removed prop) | `modules/builder/components/PublicPageContent.vue:169` | **removed** | rename to `innerHTML`, as upstream 2.3.3 does |
| ↳ `bodyAttrs`, `htmlAttrs`, `titleTemplate` | `core/layouts/login.vue:18`, `database/pages/form.vue:231`, `arabase/plugin.js:41-45` | supported (Capo.js sorting now default) | none |
| `import.meta.client` / `import.meta.server` | ~24 files, e.g. `core/middleware/authenticated.js:8`, `plugins/clientHandler.js:566`, `store/job.js:115` | canonical in v3+v4 | none |
| `import.meta.dev` | `sentry.client.config.ts`, `sentry.server.config.ts` | unchanged | none |
| `process.client` / `process.server` / `process.browser` | **no matches** | removed/deprecated | none — already migrated |
| `nuxtApp.$store` / `$registry` / `$client` / `$i18n` / `$bus` / `$realtime` / `$config` / `$router` | throughout, e.g. `core/middleware/settings.js:6`, `core/pages/settings.vue:41,61,105`, `test/helpers/testApp.js:341` | unchanged | none |
| `nuxtApp.provide` / `vueApp.component` / `vueApp.directive` | `core/plugins/bus.js:29`, `builder/plugins/global.js:21-37`, `arabase/plugin.js:27` | unchanged | none |
| `runWithContext` | `core/middleware/authentication.js:35`, `arabase/pages/publicPageView.vue:69` | unchanged | none |
| `nuxtApp.hook('app:rendered')` + `nuxtApp.payload.vuex` | `core/plugins/vuexState.js:13-14,22,31` | `payload` still supported; only `window.__NUXT__` was removed (no matches in fork) | none |
| `nuxtApp.hooks.hookOnce('page:finish')` | `core/utils/routing.js:12` | unchanged | none |
| `import.meta`-free `useRequestEvent()` | 6 middlewares: `authenticated.js:8`, `authentication.js:10`, `impersonate.js:11`, `pendingJobs.js:8`, `settings.js:5`, `staff.js:8`, `urlCheck.js:14` | unchanged | none |
| `useRequestURL()` | `builder/pages/publicPage.vue:50`, `core/plugins/isWebFrontendHostname.js:10` | unchanged | none |
| `$fetch` | **no matches** (fork uses its own axios `$client`) | unchanged | none |
| `useRoute` / `useRouter` | imported from `vue-router` in ~20 files (e.g. `builder/pages/pageEditor.vue:32`) plus `useRouter` from `#app` | unchanged | none |
| `route.meta.name` / `.meta.path` | **no matches** (v4 dedupes these onto the route) | would break | none |
| `to.meta.useRouteWorkspaceParam` | `core/middleware/workspacesAndApplications.js:20` | custom meta keys survive | none |
| `definePageMeta` (incl. `name:`) | 6 `core/pages/*`, 4 `arabase/pages/*`, builder/automation/admin pages | `scanPageMeta` now defaults to `'after-resolve'`, i.e. meta is scanned **after** `pages:extend` | favourable for module-provided pages (fork has no root `pages/` dir); verify layout/middleware still apply |
| `pages/` convention | no root `pages/` at all; routes pushed via `extendPages` in each `modules/*/module.js`; `pages: true` set explicitly at `config/nuxt.config.base.ts:50` | `pages` option still supported (`@nuxt/schema@4.4.8` L975-979; `nuxt@4.4.8` L1188-1191) | keep `pages: true`; `srcDir` heuristic would also return true, but explicit is safer |
| `runtimeConfig` | set in `config/nuxt.config.base.ts:55-59` and `modules/core/module.js:55-90`; read by `useRuntimeConfig()` in ~10 files | unchanged; v4 merely adds `runtimeConfig.app.{buildId,baseURL,buildAssetsDir,cdnURL}` defaults | none |
| `app.config` / `useAppConfig` | only `sentry.client.config.ts:1,7,60` (`appConfig.sentry?.config`); no `app.config.ts` file | unchanged; v4 emits `types/app.config.d.ts` | none |
| `plugins/` ordering | every plugin declares `name` + `dependsOn` (`core/plugins/{store,vuexState,clientHandler,permissions,realTimeHandler,storeRegister}.js`, `automation/plugins/realtime.js:5`, `builder/plugins/realtime.js:5`, `builder/plugin.js:154`, `arabase/plugin.js:23`, `arabase/registryPlugin.js:36`); call order in `modules/core/module.js:114-137` | unchanged | none |
| `experimental.` flags | only `experimental.appManifest` (`config/nuxt.config.base.ts:141-143`) | still supported; `treeshakeClientOnly`, `configSchema`, `polyfillVueUseHead`, `respectNoSSRHeader` were **removed** but the fork uses none of them (greps empty) | none |
| `@nuxt/kit` in `modules/*/module.js` | `core` from `@nuxt/kit`; `automation/builder/dashboard/database/integrations/arabase` from `nuxt/kit` | both specifiers valid in v4 | none |
| `nuxt.hook('vite:extendConfig')` | `modules/builder/module.js:50-53` (`config.server.allowedHosts = true`) | deprecated only at `compatibilityVersion: 5` (Vite Environment API) | works at v4; flag as future work |
| `nuxt.hook('nitro:config')` | `modules/core/module.js:100-105`, `config/nuxt.config.dev.ts:12-19` | unchanged | none |
| `nuxt.options.{alias,css,runtimeConfig,app.head}` | `core/module.js:43,46,55-90,199,202`, `arabase/module.js:41-48` | unchanged | none |
| `defineNuxtConfig` keys in use | `compatibilityDate, pages, alias, css, runtimeConfig, modules, i18n, nitro, vite.*, buildDir, build.{transpile,cache,cacheDirectory}, experimental.appManifest, vue.compilerOptions.comments, devtools, hooks, sourcemap, features.inlineStyles, i18n.experimental.*, nitro.preset` | all retained by 2.3.3 under Nuxt 4, except the top-level `generate` key (fork does not use it) and the four removed experimentals | none, but see Risk 4 |
| `new Nuxt(config)` / `new Builder(nuxt)` from `'nuxt'` | `test/helpers/create-nuxt.js:1,6,9`, consumed by `test/server/core/pages/server.spec.js:5,39,44-46` | **removed** — `nuxt@4.4.8` exports only `{ build, createNuxt, loadNuxt }` | rewrite the helper with `createNuxt`/`loadNuxt`, or delete helper+spec (upstream chose the latter: `exclude: ['**/test/server/**']`) |
| `mountSuspended` / `@nuxt/test-utils/runtime` | 30 spec files (`test/helpers/testApp.js:20`, `test/unit/arabase/*.spec.js`, …) | kept in test-utils 4 | none |
| `environmentOptions.nuxt.{domEnvironment,overrides}` | `vitest.config.base.ts:33-56` | kept by test-utils 4 (2.3.3's own config still uses `overrides`) | none |
| `defineVitestConfig` | `vitest.config.ts:1-4` | same import path `@nuxt/test-utils/config` | none |
| `useAsyncData`/`useError`/`useSeoMeta`/`useHeadSafe`/`useNuxtData`/`refreshNuxtData`/`abortNavigation`/`setPageLayout`/`useLoadingIndicator`/`NuxtTime`/`NuxtRouteAnnouncer`/`defineNuxtComponent` | **no matches** | — | none |

---

## Alias and env-remap mirrors

### `@jadawel` alias — declaration sites and every mirror

| # | Path | Line | Kind | Nuxt-4 action |
|---|---|---|---|---|
| 1 | `web-frontend/config/nuxt.config.base.ts` | 51-53 | `alias: { '@jadawel': '' }` | none (empty string is resolved against rootDir) |
| 2 | `web-frontend/modules/core/module.js` | 46 | `nuxt.options.alias['@jadawel'] = resolve('../../')` | none — the load-bearing declaration |
| 3 | `web-frontend/jsconfig.json` | 5, 11 | `paths."@jadawel/*"`, `resolve.alias."@jadawel"` | none (IDE only) |
| 4 | `web-frontend/vitest.config.base.ts` | 61 | `'@jadawel_test_cases'` only | none; the Nuxt alias arrives via `environment: 'nuxt'` → nixt config |
| 5 | `web-frontend/vitest.setup.ts` | 63-65 | `vi.mock('@jadawel/modules/core/utils/string')` | none |
| 6 | `web-frontend/intellij-idea.webpack.config.js` | 16-17 | both aliases | none |
| 7 | `web-frontend/jest.config.js` | 9-11 | `moduleNameMapper` (`^@jadawel/(.*)$` etc.) | none (legacy jest config, unused by CI) |
| 8 | `tests/jsconfig.json` | 5 | `@jadawel_test_cases/*` | none |
| gen | `web-frontend/.nuxt/tsconfig.json` 128-131, `.nuxt/tsconfig.server.json` 134-137 | — | generated by `nuxt prepare` | **regenerated**: Nuxt 4 emits `tsconfig.{app,server,shared,node}.json`; the two old files disappear |
| gen | `web-frontend/.nuxt/eslint.config.mjs` | — | consumed by root `eslint.config.mjs` | path unchanged under `@nuxt/eslint` 1.16 |

Nuxt 4 does not change alias semantics; per its config docs, aliases are still auto-injected
into the generated TypeScript configs. Nothing in this list needs an edit beyond accepting the
regenerated `.nuxt/` files. `PATCHES.md` (Phase 2) records the same six hand-written mirrors.

### `env-remap.mjs` — role and Nuxt-4 exposure

Fork role (three jobs, all local to the file):
1. `process.env.NITRO_CLUSTER_WORKERS ||= '1'` — bounds the node-cluster worker pool used by
   `nitro.preset: 'node-cluster'` in `config/nuxt.config.prod.ts`.
2. A prelude that copies every `BASEROW_*` var to its `JADAWEL_*` spelling (mirrors
   `backend/src/jadawel/config/legacy_env.py`).
3. The `envMapping` table (legacy names → `NUXT_*`), plus special cases for
   `JADAWEL_PUBLIC_URL`, `JADAWEL_EMBEDDED_SHARE_URL`, `JADAWEL_EXTRA_PUBLIC_URLS`,
   `JADAWEL_BUILDER_DOMAINS`, and the positive-integer guard on
   `JADAWEL_MAX_FIELD_TEXT_LENGTH`.

Loaded via `node --import ./env-remap.mjs` from the `dev`, `preview` and `prod` scripts and
from `web-frontend/docker/docker-entrypoint.sh` (`nuxt-prod`), and from
`docker/docker-entrypoint-prod.sh`. It is **not** loaded by `postinstall` (`APP_ENV=dev nuxt prepare`).

**Does Nuxt 4 change runtimeConfig env handling?** No. Nuxt 4 keeps c12/exsolve with the
`NUXT_` prefix and `_`-nested keys (`NUXT_PUBLIC_*` → `runtimeConfig.public.*`); the only
runtimeConfig delta is the new `runtimeConfig.app.{buildId,baseURL,buildAssetsDir,cdnURL}`
defaults (`@nuxt/schema@4.4.8` `common.ts` `runtimeConfig.$resolve`), which no fork mapping
targets. `NUXT_DEFAULT_LOCALE` is read with `process.env` at config-load time in
`nuxt.config.base.ts:66`, independent of the runtimeConfig system. Conclusion: **no edit to
`env-remap.mjs`**, and no new `NUXT_*` key is introduced by the upgrade. Re-verify after the
bump only because the whole point of the file is to be the single place env resolution is
documented.

---

## Files to change

Ordered; every entry names the concrete edit.

1. `web-frontend/package.json`
   - `nuxt`: `3.21.10` → `^4.4.2`.
   - `@nuxt/test-utils`: `^3.21.0` → `^4.0.2`; `@nuxt/eslint`: `^1.12.1` → `^1.15.2`;
     `vitest` `^4.0.17` → `4.1.9`; both `@vitest/coverage-*` → `4.1.9`;
     `globals` `^17.0.0` → `^17.7.0`.
   - Storybook: either (a) `@nuxtjs/storybook` → `npm:@nuxtjs/storybook@nightly`,
     `storybook`/`addon-docs`/`addon-links` → `10.3.5`, or (b) keep storybook out of the
     Nuxt-4 commit entirely (it is not on the app's runtime path).
   - Add the four `resolutions` pins from `## Dependency groups` A.
   - Do **not** import `xlsx`, `posthog-js@^1.232.4`, or downgrade `vue-router` — those are
     the other direction: fork values win.
2. `web-frontend/yarn.lock` — regenerate (`yarn install`), never hand-edit.
3. `web-frontend/config/nuxt.config.base.ts` — add `srcDir: '.'`; bump `compatibilityDate`
   to `2025-11-15`; optionally adopt the `${frontendCookiePrefix}i18n-language` cookie key
   (the fork hardcodes `i18n-language` today, L77).
4. `web-frontend/tsconfig.json` — replace with the four project references.
5. `web-frontend/server/tsconfig.json` — optional delete (redundant with project refs).
   Keep `web-frontend/server/routes/_health.get.ts` — fork-only, health-probe target.
6. `web-frontend/vitest.config.base.ts` — add `testTimeout: 30_000`, `hookTimeout: 120_000`,
   and `'**/test/server/**'` to `exclude`.
7. `web-frontend/test/helpers/create-nuxt.js` — rewrite to
   `import { createNuxt, loadNuxt } from 'nuxt'` (or delete it together with
   `test/server/core/pages/server.spec.js`).
8. `web-frontend/modules/core/module.js` — delete `compatibility: { nuxt: '^3.0.0' }` (L28-32).
9. `web-frontend/modules/builder/module.js` — delete the same block (L16-18).
10. `web-frontend/modules/dashboard/module.js` — delete the same block (L41-43).
11. `web-frontend/modules/core/head.js` — replace `hid: true` on the four favicon links
    (L22,29,36,43) with the named `key: 'favicon-16' | 'favicon-32' | 'favicon-64' | 'favicon-192'`
    used by upstream 2.3.3, and port `modules/builder/utils/favicon.js`
    (`getDefaultFaviconKeys` + `getCustomFaviconLinks`) — it does not exist in the fork or in 2.2.2.
12. `web-frontend/modules/builder/components/PublicPageContent.vue` — L141 `hid: true` →
    derived `key`; L169 `style: [{ children: … }]` → `innerHTML`; replace the inline
    `faviconLink` computed with `getCustomFaviconLinks(props.builder)` + `faviconLinks`
    (upstream 2.3.3 shape) and set `header.link` unconditionally when non-null.
13. `web-frontend/.storybook/main.ts` — add upstream's `viteFinal` `optimizeDeps` block only if
    storybook stays.
14. `web-frontend/Dockerfile` — `ARG NODE_BASE_IMAGE="node:24.18.0-trixie-slim"`.
15. `PATCHES.md` — append a "Phase — Nuxt 4" section (the fork documents every upstream-derived
    change there; the removed `compatibility` blocks and the Unhead prop migration belong in it).
16. `docs/UPSTREAM_2_3_RESEARCH.md` — its "Nuxt 4 | Missing | `web-frontend/package.json` pins
    Nuxt `3.21.10`" row becomes stale; update it in the same commit.

Explicitly **not** changed: `web-frontend/env-remap.mjs`, `web-frontend/eslint.config.mjs`
(only its devDependency), `web-frontend/config/nuxt.config.{dev,test,prod}.ts`,
`web-frontend/i18n.config.ts`, `web-frontend/jsconfig.json`, `web-frontend/vitest.config.ts`,
`web-frontend/vitest.setup.ts`, `web-frontend/stylelint.config.mjs`, `web-frontend/jest.config.js`,
`web-frontend/modules/{database,automation,integrations,arabase}/module.js`,
`web-frontend/config/locales.js`.

---

## Risk notes

1. **Disabling `core` silently kills the app (highest severity).** The three
   `compatibility: { nuxt: '^3.0.0' }` blocks make `@nuxt/kit` skip `setup()` entirely for
   `core`, `builder` and `dashboard` under Nuxt 4. There is no error by default (only a
   `logger.warn`, plus a throw if `experimental.enforceModuleCompatibility` is enabled) — the
   first symptom is an app with no `@jadawel` alias, no plugins, no layouts. Delete all three
   in the same commit as the version bump.

2. **`create-nuxt.js` is a hard break, not a warning.** `nuxt@4.4.8`'s public exports are
   `{ build, createNuxt, loadNuxt }` only — `Nuxt` and `Builder` are gone. The fork's helper
   is imported by one spec whose four tests are already `test.skip`. Upstream's resolution was
   to exclude `**/test/server/**` in vitest and leave the dead helper. Choose one; do not leave
   the import in place, because the file is loaded at collection time by any future spec that
   imports it.

3. **`vue-router` de-duplication changes which router the app runs on.** Today the fork has
   top-level `vue-router@5.3.0` and `nuxt/node_modules/vue-router@4.6.4` — Nuxt 3 internals use
   v4. With Nuxt 4.4.8 (`vue-router ^5.1.0`) that nested copy disappears and everything shares
   v5.3.0. The fork's direct usages (`onBeforeRouteUpdate`, `onBeforeRouteLeave`, `useRoute`,
   `useRouter`, `route.matched`, `RouterViewPlaceholder`) exist in v5, but this is a real
   behavioural swap in the router internals and deserves an explicit dev-server + e2e pass
   rather than a "no code change needed" assumption.

4. **`build.cache` / `build.cacheDirectory` are not verified against the Nuxt 4 schema.** I
   confirmed upstream 2.3.3 retains both keys while running Nuxt 4 (strong evidence they are
   accepted), but `@nuxt/schema@4.4.8`'s generated `.d.mts` had to be fetched from the registry
   and my searches for `cacheDirectory`/`buildCache` in it returned nothing conclusive
   [INFERENCE]. If `nuxt prepare` emits an "Unknown config key" style warning for them, that is
   a maintenance note, not a break — the fork's `build.cacheDirectory` only steers the cache root.

5. **Unhead v2 removes `hid` and `children`.** The fork uses `hid: true` in five places and
   `style[].children` once. Unhead v2 tolerates them only with `unhead: { legacy: true }`;
   without the migration the favicon tags lose their dedupe key (the builder's custom favicon
   silently appends instead of overriding the defaults) and the theme `style` tag may not
   render. Port upstream's `builder/utils/favicon.js` rather than inventing a new scheme — the
   keys are deliberately derived from `head.js`.

6. **Storybook 9.0.1 cannot run under Nuxt 4.** `@nuxtjs/storybook@9.0.1` → `@storybook-vue/nuxt@9.0.1`,
   peer `nuxt: ^3.13.0`, `storybook: ~9.0.5`. The upgrade path is the `nightly` npm alias
   (which peers `storybook ~10.0.2` and depends on `@nuxt/kit ^3.18.1 || ^4.0.0`), i.e. two
   major-version jumps at once. `yarn storybook` and `nuxt-dev-with-storybook` break otherwise;
   the app build and the test suite do not depend on storybook, so this can be a follow-up.

7. **The 2.3 package diff must not be ported wholesale.** `xlsx` arrives from
   `cdn.sheetjs.com` (not the yarn registry) and drags the whole Excel-import feature
   (`modules/database/utils/excel.js`, `TableExcelImporter.vue`, importer registration,
   locale strings, backend tasks). Importing it "because it is in the same package.json hunk"
   would pull an unrelated, supply-chain-sensitive feature into a router/framework migration.

8. **`@nuxt/test-utils` 4 raises the peer floor to `vitest ^4.0.2` and `happy-dom >=20.0.11`.**
   The fork satisfies both (`vitest ^4.0.17` → 4.1.2 installed; `happy-dom ^20.8.9`), but the
   bump must land together with the vitest bump, not before it.

9. **`scanPageMeta` now runs after `pages:extend`.** This is the Nuxt 4 default and is
   favourable for the fork (all routes come from `extendPages` in modules, and there is no root
   `pages/` dir). The risk is only if a future `pages:extend` hook wanted to rewrite page meta —
   that must move to `pages:resolved`. No such hook exists today; noted so it is not added later.

10. **Fork-only safety rails must survive the merge.** The `langDir: '../locales'` +
    `pages: true` + `defaultLocale: 'ar'` edits in `nuxt.config.base.ts`, the
    `patch-datepicker-locale.mjs` `postinstall` step, the arabase module entry, the production
    Nitro `node-cluster` preset with `NITRO_CLUSTER_WORKERS ||= '1'`, `features.inlineStyles: false`
    and `sourcemap.client: 'hidden'` are all fork divergences that upstream 2.3.3 does not have.
    A naive "take upstream's file" merge deletes them. The i18n `langDir` in particular is
    load-bearing: `@nuxtjs/i18n@10.2.4` resolves a layer `langDir` against
    `resolve(rootDir, restructureDir='i18n')`, so `'../locales'` lands on
    `web-frontend/locales` and needs no symlink — which is exactly why `web-frontend/i18n/locales`
    was removed from git (`PATCHES.md`, Windows-safe i18n section).