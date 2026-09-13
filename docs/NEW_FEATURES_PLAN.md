# Jadawel upstream 2.3 feature port plan

Status: planned on branch `new_features`

Baseline: Jadawel `2.2.2`-derived source at commit `e14f16335619`

Compatibility target: the OSS/core portions of upstream Baserow `2.3.3`

Research input: [`UPSTREAM_2_3_RESEARCH.md`](UPSTREAM_2_3_RESEARCH.md)

## Goal

Bring these capabilities into Jadawel while preserving the Arabic-first RTL UI,
the `jadawel.*` namespace, existing fork features, and the deliberate absence of
`premium/` and `enterprise/` packages:

1. Direct `.xlsx`, `.xls`, and `.ods` import, plus `.xlsx` and `.ods` export.
2. Collapsible Group By sections, per-group aggregates, and up to five levels.
3. Responsive Application Builder column layouts and burger menus.
4. New runtime formula functions and duration support.
5. Nuxt 4.
6. General caching enabled by default.
7. Python 3.14.6 container images for the upstream memory fix.
8. Row moves that do not modify `updated_on`.

Item 8 is interpreted as the upstream 2.3 breaking change: moving a row changes
only its order and must not make Last Modified fields appear changed.

## Scope decisions

- Port from upstream `2.3.3`, not only `2.3.0`, so the 2.3 patch fixes are included
  wherever they touch one of these features.
- Import is an upstream OSS feature. Spreadsheet **export is additional Jadawel
  work**; upstream 2.3 core still has only the CSV table exporter.
- Export computed/displayed cell values, not executable spreadsheet formulas.
  Text beginning with `=`, `+`, `-`, or `@` must remain text to prevent formula
  injection when a downloaded workbook is opened.
- Do not copy or import upstream Advanced/Enterprise Code or XLS workflow actions.
  They are outside this plan and conflict with the fork's OSS-only policy.
- Prefer additive registrations under `arabase/`. Where a feature changes existing
  core models, stores, or handlers and no extension seam exists, make the smallest
  core edit and record every affected upstream-derived file in `PATCHES.md`.
- Every new UI string must ship in English and Arabic. Layout work must be verified
  in Arabic RTL and English LTR and use logical CSS properties.

## Delivery strategy

Land the work as independently reviewable commits. Do not combine the global Nuxt
migration with a user-facing feature. Each phase must be green before the next one
starts.

| Phase | Deliverable | Depends on |
| --- | --- | --- |
| 0 | Freeze the port map and baseline tests | Nothing |
| 1 | Python 3.14.6, cache default, row-move semantics | Phase 0 |
| 2 | Nuxt 4 migration | Phase 0 |
| 3 | Runtime formulas and duration support | Phases 1-2 |
| 4 | Excel/ODS import and export | Phases 1-2 |
| 5 | Enhanced Group By | Phases 1-2 |
| 6 | Responsive columns and burger menus | Phases 2-3 |
| 7 | Cross-feature regression, image publication, deployment handoff | Phases 1-6 |

Phases 3, 4, and 5 can be developed as separate commits after the Nuxt 4 migration,
but they should be integrated one at a time to keep failures attributable.

## Phase 0 — baseline and port map

- [ ] Obtain the official upstream `2.3.3` source archive and verify its tag/release
  provenance.
- [ ] Diff upstream `2.2.2..2.3.3` for only the modules named in this plan. Do not
  attempt a repository-wide merge because the fork-wide `baserow` to `jadawel`
  rename exceeds reliable rename detection.
- [ ] Classify every candidate file as core OSS, premium, or enterprise. Only core
  OSS code is eligible for a direct adapted port.
- [ ] Record upstream migrations and their dependency order. Create new Jadawel
  migrations against the local migration heads instead of copying dependency names
  blindly.
- [ ] Run and record the current focused backend/frontend tests, Arabic locale
  parity, and fork-hygiene test so later regressions have a baseline.
- [ ] Add acceptance fixtures: multilingual workbook data, a five-level grouped
  table, a responsive Builder page, duration expression cases, and a row with Last
  Modified fields.

Exit criterion: a file-by-file port map identifies core changes, additive changes,
migrations, tests, translations, and relevant `2.3.1`-`2.3.3` fixes.

## Phase 1 — backend/runtime foundation

### Python 3.14.6

- [ ] Change all Python runtime images from `3.14.3-slim-trixie` to
  `3.14.6-slim-trixie` in `backend/Dockerfile`, `deploy/all-in-one/Dockerfile`, and
  both stages of `embeddings/Dockerfile`.
- [ ] Rebuild backend, all-in-one, and embeddings images. Confirm native wheels and
  compiled dependencies still install on Python 3.14.6.
- [ ] Smoke-test Django startup, migrations, Celery, Channels, and the embeddings
  health endpoint.

Acceptance: all runtime containers report Python 3.14.6 and the normal health checks
pass with no increase in steady-state worker memory during a representative import.

### Default caching

- [ ] Change `JADAWEL_CACHE_TTL_SECONDS` from `0` to `120` in
  `backend/src/jadawel/config/settings/base.py`, matching upstream 2.3.
- [ ] Keep `0` as the documented emergency switch that disables this cache.
- [ ] Audit settings, user, and database-token cache invalidation paths before
  enabling the default. Verify multi-process behavior against Redis, not only a
  local-memory cache.
- [ ] Update configuration/deployment documentation and examples where the old
  default is stated or implied.
- [ ] Add tests for the default value, cache hits, invalidation after mutation, and
  explicit opt-out with `JADAWEL_CACHE_TTL_SECONDS=0`.

Acceptance: a default deployment caches for 120 seconds, mutations invalidate stale
entries, and setting the value to 0 restores uncached behavior.

### Move rows without changing `updated_on`

- [ ] In the row move handler, persist `order` only instead of `order` and
  `updated_on`.
- [ ] Preserve permission checks, dependency recalculation, realtime row movement,
  audit/action history, and webhooks.
- [ ] Add backend tests covering move-before, move-to-end, API moves, undo/redo, and
  views. Assert that `updated_on`, Last Modified fields, and formulas based on Last
  Modified are unchanged while order-dependent lookup data still refreshes.
- [ ] Document this as an API behavior change and add the core file to `PATCHES.md`.

Acceptance: every row-move entry point changes ordering without changing the row's
modification timestamp or falsely marking it as edited.

## Phase 2 — Nuxt 4 migration

- [ ] Adapt upstream's Nuxt 4 dependency set as a coherent group, starting from
  `nuxt ^4.4.2`, `@nuxt/eslint ^1.15.2`, and `@nuxt/test-utils ^4.0.2` rather than
  updating only the `nuxt` package.
- [ ] Refresh `yarn.lock` using the repository's pinned Node 24/Yarn toolchain.
- [ ] Port the upstream configuration changes into local `nuxt.config.*`, SSR,
  Nitro, test, i18n, and module-loading configuration while retaining `@jadawel`
  aliases and environment remapping.
- [ ] Audit deprecated Nuxt 3 APIs, page metadata, middleware, auto-imports,
  plugins, runtime config, server routes, and test helpers.
- [ ] Verify all custom modules under `web-frontend/modules/arabase/`, especially
  plugin ordering and registry initialization.
- [ ] Update architecture and developer documentation that still claims Nuxt 3.
  If `AGENTS.md` or a skill is edited, follow the repository's agent-documentation
  workflow before changing it.
- [ ] Log unavoidable changes to upstream-derived core files in `PATCHES.md`.

Verification:

- [ ] Frontend unit tests and lint.
- [ ] SSR smoke tests for login, workspace/table, public view, Builder preview, and
  custom Arabase routes.
- [ ] Production build with the same memory limits used by the image workflow.
- [ ] Arabic locale parity and browser checks in both RTL and LTR.
- [ ] No hydration warnings, duplicate plugin registration, or missing runtime
  configuration in browser/server logs.

Exit criterion: the existing application behaves the same on Nuxt 4 before any new
feature UI is layered onto it.

## Phase 3 — runtime formulas and duration support

- [ ] Port the upstream core runtime formula types and argument validation for:
  `abs`, `range`, `to_json`, `from_json`, `null`, `number_format`, `to_duration`,
  `duration_format`, and `to_datetime`.
- [ ] Port shared duration parsing/formatting utilities and the duration runtime
  value type used by Builder, integrations, and automations.
- [ ] Confirm exact function names and signatures from `2.3.3`; use
  `duration_format`, which is the upstream source identifier, even though release
  prose also called it `format_duration`.
- [ ] Wire the functions into backend and frontend registries, autocomplete,
  validation, help text, and serialized formula definitions.
- [ ] Add English and Arabic names, descriptions, examples, validation messages,
  and duration-format labels.
- [ ] Cover null propagation, timezone-aware datetimes, negative and fractional
  durations, invalid formats, JSON escaping, large ranges, and locale-independent
  number formatting.
- [ ] Add an explicit maximum for `range` output to prevent expressions from
  allocating unbounded lists.

Acceptance: the same expression returns compatible typed results in preview and
backend execution, duration inputs render consistently across desktop/tablet/mobile,
and invalid expressions fail with translated, actionable messages.

## Phase 4 — Excel/ODS import and export

### Import

- [ ] Add the upstream SheetJS `xlsx 0.20.3` dependency using the pinned official
  distribution and record its license/provenance.
- [ ] Port the Excel importer type, parser utility, component, previews, sheet
  selector, first-row-header choice, and registration.
- [ ] Support `.xlsx`, legacy `.xls`, and `.ods` for both creating a new table and
  importing into an existing table.
- [ ] Preserve upstream preview limits, configured upload limits, asynchronous job
  progress/cancellation, field mapping, and error reporting.
- [ ] Load the parser lazily so ordinary table pages do not pay the spreadsheet
  bundle cost.
- [ ] Add Arabic/English translations and verify long Arabic filenames, RTL sheet
  names, mixed Arabic/Latin cell data, dates, booleans, numbers, sparse rows,
  duplicate/empty headers, multiple sheets, and malformed/password-protected files.

### Export

- [ ] Implement additive `xlsx` and `ods` table exporter types through the existing
  backend/frontend exporter registries. Reuse the export job, permissions, storage,
  progress, cancellation, and download lifecycle instead of downloading all rows
  into the browser.
- [ ] Use the installed `openpyxl` write-only mode for `.xlsx`. Select and pin a
  maintained ODS writer only after its license and memory behavior pass a focused
  spike; add it to `backend/pyproject.toml` and `uv.lock` if accepted.
- [ ] Match current CSV export semantics for selected view, filters, sorts, field
  visibility, optional Row ID/primary field, link/file display values, and public
  export permissions.
- [ ] Sanitize workbook filenames and sheet names, preserve Unicode/Arabic, cap
  spreadsheet dimensions, and store untrusted leading formula characters as text.
- [ ] Stream/write incrementally to a temporary file so large exports do not hold
  the full table in either the web worker or browser memory.
- [ ] Test download MIME types, extensions, cancellation/cleanup, empty tables,
  maximum-size handling, all field types, Arabic data, and round trips back through
  the importer.

Acceptance: users can directly import supported spreadsheet files and export a
filtered view as `.xlsx` or `.ods`; a representative large job stays within the
worker memory budget and its file can be opened by Excel and LibreOffice.

## Phase 5 — enhanced Group By

- [ ] Port the grouped-query and aggregate backend changes needed to return group
  paths, counts, aggregate values, and rows correctly at up to five nesting levels.
- [ ] Enforce the five-level limit server-side as well as in the UI.
- [ ] Port collapse/expand state, group banners, rendering utilities, virtual-scroll
  offset handling, and collapse-all/expand-all controls.
- [ ] Port per-group aggregation selection and rendering, reusing the existing view
  aggregation registry and permission checks.
- [ ] Port drag ordering for Group By rules where required by the five-level editor.
- [ ] Preserve public-view restrictions and ensure collapsed groups never leak
  hidden rows or aggregate values to an unauthorized viewer.
- [ ] Add Arabic/English labels and verify indentation, chevrons, drag handles,
  keyboard navigation, and virtual scrolling in RTL and LTR.

Tests must cover null groups, all supported field types, empty groups, nested groups,
aggregate changes after row edits, row movement, filtering/search/sorting, pagination,
public views, concurrent updates, and large datasets.

Acceptance: a grid can group by one through five fields; each group can be collapsed
independently; group aggregates remain correct; scrolling and row selection do not
jump or address the wrong row.

## Phase 6 — responsive Builder columns and burger menus

- [ ] Add the upstream Column element fields and validation for `layout_type`,
  `column_weights`, and per-device `column_stacking`, using a local migration based
  on upstream migration `builder/0072_columnelement_layout_options.py`.
- [ ] Port preset ratios, custom weights, one-to-six-column validation, device
  selectors, and stacked/horizontal rendering for desktop, tablet, and smartphone.
- [ ] Add the Menu element's per-device expanded/compact `variant`, adapting
  upstream migration `builder/0069_menuelement_variant.py` to the local migration
  graph.
- [ ] Port burger styling, open/close state, click-outside behavior, editor preview,
  focus management, keyboard controls, and page-preview locking.
- [ ] Migrate existing Column and Menu rows to defaults that preserve their current
  desktop rendering. Supply reversible migration behavior where data preservation is
  possible.
- [ ] Verify nested columns/elements, drag and drop, element duplication, undo/redo,
  page export/import, publish/preview, and public pages.
- [ ] Add Arabic/English strings and test burger panel placement, close controls,
  alignment, and menu hierarchy in RTL and LTR at all breakpoints.

Acceptance: authors can choose presets or custom column weights and stacking per
device; published menus switch to an accessible burger presentation on configured
devices without changing existing pages unexpectedly.

## Phase 7 — integration, release, and deployment handoff

- [ ] Run database migrations on a copy of production-like data and verify rollback
  strategy before deployment.
- [ ] Run focused tests for every phase, then the full backend/frontend suites,
  lint, Arabic locale parity, and `pytest tests/arabase -q` fork-hygiene gate.
- [ ] Confirm neither `baserow_premium` nor `baserow_enterprise` is importable and
  no prohibited source was introduced.
- [ ] Run browser journeys for spreadsheet import/export, five-level grouping,
  responsive Builder pages, duration formulas, and row moving in Arabic and English.
- [ ] Profile memory during large import/export, grouped scrolling, Nuxt SSR, Django,
  and Celery jobs. Compare against the Phase 0 baseline.
- [ ] Run dependency/license and vulnerability checks for SheetJS and the selected
  ODS writer.
- [ ] Refresh the `graft` graph after the large code changes when the `graft` tool is
  available.
- [ ] Publish a new all-in-one image, then update the root `Dockerfile` image digest
  and follow `docs/DEPLOY_CRANL.md`. A source push alone does not deploy Jadawel.
- [ ] Verify the live image version, health endpoints, cache behavior, static assets,
  migrations, and one real user flow before declaring completion.

## Required gates for every feature commit

- Focused backend or frontend unit tests pass.
- New and changed user-facing keys exist in both `en.json` and `ar.json`.
- Arabic RTL and English LTR behavior is checked for UI changes.
- Permission tests cover allowed, denied, unauthenticated, and cross-workspace users
  where an API boundary changes.
- Any core-file edit is explained in `PATCHES.md`.
- No global `baserow` replacement is used; notices, upstream URLs, and historical
  migration identifiers are preserved where required.
- No deployment is claimed until the image publish, digest bump, redeploy, and live
  verification steps are complete.

## Proposed commit sequence

1. `docs(upstream): plan 2.3 feature ports`
2. `chore(runtime): update Python images to 3.14.6`
3. `perf(cache): enable the general cache by default`
4. `fix(database): preserve updated timestamp when moving rows`
5. `chore(frontend): migrate to Nuxt 4`
6. `feat(formula): add runtime conversions and duration support`
7. `feat(database): import Excel and ODS files`
8. `feat(database): export XLSX and ODS workbooks`
9. `feat(database): expand grouped grid views`
10. `feat(builder): add responsive columns and burger menus`
11. `test(release): verify upstream 2.3 feature integration`

## Definition of done

All eight requested items meet their acceptance criteria; migrations succeed on an
existing installation; full CI, locale parity, and fork hygiene pass; deployment
documentation reflects the new runtime; and a published, digest-pinned image has
been verified on CranL. Until the publication and redeployment steps are explicitly
authorized and completed, the branch is implementation-ready but not deployed.
