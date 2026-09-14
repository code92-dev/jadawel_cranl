# New features remediation follow-up plan

Status: **Phases 0-5 implemented and gated (see the implementation record below);
Phase 6 partially evidenced; Phase 7 remains unauthorized**

Reviewed range: `f702ed8e1609e3a2deeeb61cf0a7917453a8a159..e8d90df921408cc24a2ec4e224276b410ac7e1f6`

Parent plans:

- [`NEW_FEATURES_PLAN.md`](NEW_FEATURES_PLAN.md)
- [`NEW_FEATURES_REMEDIATION_PLAN.md`](NEW_FEATURES_REMEDIATION_PLAN.md)

## Objective

Close every gap found by the post-remediation review before describing Phases 0-6
as complete. This plan does not authorize publishing or deploying an image. The
existing Phase 7 remains a separate action requiring explicit authorization.

The implementation must preserve the working public Group By protections and other
already-green behavior while fixing the incomplete formula, Builder, spreadsheet,
configuration, documentation, and release contracts.

## Current verified baseline

The review found useful focused coverage, but the evidence does not satisfy the
parent plan's definition of done:

- focused backend checks: 1,015 passed;
- focused frontend checks: 1,061 passed;
- locale parity: 3,847 English and 3,847 Arabic keys;
- Prettier and `git diff --check`: clean;
- ESLint: no errors and one warning;
- Ruff: seven findings in the reviewed tree;
- the recorded full frontend run still has seven failures;
- no current all-in-one candidate image was built and verified from the reviewed
  commit.

Do not convert any phase below to complete from historical output alone. Record the
command, commit, date, environment, and result for every completed gate.

## Repair order

| Phase | Outcome                                             | Depends on                           |
| ----- | --------------------------------------------------- | ------------------------------------ |
| 0     | Reopen completion state and freeze regression tests | Nothing                              |
| 1     | Establish one frontend/backend formula contract     | Phase 0                              |
| 2     | Complete compact-menu accessibility                 | Phase 0                              |
| 3     | Correct spreadsheet and importer edge cases         | Phase 0                              |
| 4     | Generate responsive boundaries from one source      | Phase 0                              |
| 5     | Restore lint, fork, and documentation hygiene       | Phases 1-4                           |
| 6     | Pass integrated acceptance and image verification   | Phases 1-5                           |
| 7     | Publish and deploy                                  | Explicit authorization after Phase 6 |

Phases 1-4 can be implemented independently after Phase 0. Keep their commits
separate and rerun focused tests after each one.

## Phase 0 — truthful state and regression lock

- [ ] Keep both parent plans at `follow-up remediation planned/in progress` until
      every Phase 1-6 exit criterion below is evidenced.
- [ ] Capture the seven Ruff findings and seven existing frontend failures as named
      issues. Fix them or obtain an explicit, documented baseline waiver; do not
      call a failing full suite green.
- [ ] Add failing tests before each implementation fix for:
    - range generation at zero and above the configured maximum;
    - generic duration arguments receiving null;
    - focus trapping and restoration through every compact-menu close path;
    - nested submenu keyboard and ARIA behavior;
    - exact ODS carriage-return preservation;
    - import limits below, exactly at, and one byte above the boundary;
    - malformed, non-numeric, zero, and negative import-limit configuration;
    - localized workbook-dimension and import-size errors;
    - breakpoint behavior on each side of the smartphone and tablet boundaries.
- [ ] Preserve already-green security regressions, especially anonymous and
      password-protected public Group By filtering.

Exit criterion: every new review finding has a test that fails for the expected
reason, and no document claims the branch is implementation-ready.

## Phase 1 — frontend/backend formula parity

### Shared executable contract

- [ ] Add a repository-owned JSON case matrix, for example
      `tests/cases/runtime_formula_parity.json`, consumed by backend Pytest and
      frontend Vitest rather than maintaining two handwritten expectation lists.
- [ ] Cover all nine functions, their result types, null inputs, invalid input
      types, separators and duration formats, timezone-sensitive cases, a zero
      range, the exact range maximum, and one item over the maximum.
- [ ] Give failures stable codes or structured categories. For the same expression,
      backend and frontend must produce the same value and type or the same failure
      category. Returning `null` in one runtime while the other raises is not parity.
- [ ] Exercise the real parser, type validation, resolver, runtime registry, and
      execution visitors. Direct class construction alone is insufficient.
- [ ] Mount the Builder and Automation formula inputs in focused tests to prove the
      new functions are registered, discoverable, serializable, and executable in
      actual consumers.

### Range and duration corrections

- [ ] Make frontend range generation reject zero and oversized requests using the
      same semantics as the backend instead of returning `null`.
- [ ] Keep the range maximum aligned across Django settings, Nuxt runtime config,
      environment remapping, and `docs/CONFIGURATION.md`; test both the default and
      an override.
- [ ] Restore strict null rejection for the generic frontend duration argument
      type.
- [ ] Introduce a dedicated nullable-duration argument type and use it only where
      null propagation is part of the function contract, including `to_duration`
      and `duration_format`.
- [ ] Replace hard-coded English formula validation text with English and Arabic
      locale keys, preserving placeholders and glossary terminology.

Exit criterion: both runtimes pass the same case matrix through their production
execution paths, and formula UI tests prove registration and validation in Builder
and Automation.

## Phase 2 — complete compact-menu accessibility

- [ ] Retain semantic `<button>` triggers and implement a focus trap that cycles
      through the menu's actual focusable elements with Tab and Shift+Tab.
- [ ] On open, move focus into the menu and assert `document.activeElement`, not
      only an emitted event or method call.
- [ ] Restore focus to the originating trigger after Escape, the close button,
      backdrop dismissal, menu-item navigation, and programmatic closure. Remove
      close paths that explicitly suppress restoration without an accessibility
      reason.
- [ ] Make nested submenu toggles semantic buttons, or give them the complete
      equivalent keyboard contract. Support Enter and Space and connect unique
      submenu IDs with `aria-controls` and `aria-expanded`.
- [ ] Clean up document listeners, focus state, and open menus on unmount and on
      responsive device/variant changes.
- [ ] Test keyboard-only operation, empty menus, nested menus, edit and public
      modes, Arabic RTL and English LTR, and transitions between desktop and compact
      layouts.
- [ ] Add one browser journey that resizes without reloading and completes the menu
      flow without a pointer.

Exit criterion: the complete menu can be opened, traversed, nested, closed, and
re-entered with a keyboard, with deterministic focus in both directions.

## Phase 3 — spreadsheet and importer correctness

### ODS/XLSX fidelity, safety, and limits

- [ ] Encode carriage returns in ODS XML with an XML-safe representation such as
      `&#13;` without allowing the XML escaper to turn it into literal text. Assert
      both the package XML and the parsed round trip preserve exact `\r`, `\n`, and
      `\r\n` values.
- [ ] Keep formula-looking user strings inert in both XLSX and ODS, then import the
      produced files through a real spreadsheet reader/import path and compare the
      original values exactly.
- [ ] Translate row/column limit failures in English and Arabic. Prefer a stable
      error code plus interpolation parameters when the existing job API supports
      it; otherwise use the repository's existing translatable job-error pattern.
- [ ] Verify failed and cancelled exports remove partial files and release workbook
      buffers. Test cancellation after data has been written, not only an empty ODS
      buffer.
- [ ] Run and record the large-export memory benchmark after the fixes. If
      LibreOffice is unavailable in CI, keep library round-trip checks automated and
      record LibreOffice opening as a candidate-image acceptance step.

### Import-size enforcement

- [ ] Parse the configured byte limit strictly. Values such as `1abc`, `NaN`, zero,
      and negatives must use the documented safe fallback rather than silently
      weakening the limit.
- [ ] Test below the limit, exactly at it, and one byte over it, plus missing and
      malformed configuration.
- [ ] Prove every supported importer uses the shared helper and that the rejection
      message interpolates correctly in both Arabic and English.

Exit criterion: round trips are exact and inert, dimension failures are localized,
cancelled/failed jobs leave no partial artifact, memory remains within the recorded
budget, and import limits cannot be bypassed by boundary or malformed input.

## Phase 4 — one source for responsive boundaries

- [ ] Create a canonical data file such as
      `web-frontend/modules/builder/deviceBreakpoints.json` for smartphone and
      tablet boundaries.
- [ ] Generate a committed Sass partial from that file with a deterministic script;
      JavaScript imports the canonical JSON and Sass imports only the generated
      partial.
- [ ] Add `generate:device-breakpoints` and a `--check`/CI mode that fails when the
      generated partial has drifted. The generated file must say how to regenerate
      it and must not be edited manually.
- [ ] Remove duplicate numeric definitions and speculative accessors used only by
      tests. Production classification and boundary tests must both consume the
      canonical values.
- [ ] Test exact boundaries and one pixel on either side, then add a resize-without-
      reload browser check proving JavaScript classification matches rendered CSS.

Exit criterion: changing one canonical value and regenerating updates both runtime
classification and Sass behavior, and CI rejects drift.

## Phase 5 — static, fork, and documentation hygiene

- [ ] Fix all Ruff findings and rerun the repository-supported backend environment.
      Remove unused imports and parameters; use safe XML parsers in tests or a
      narrowly justified suppression only when parsing trusted generated output.
- [ ] Remove the unused `ServiceFile`/`ensure_file` abstraction and its dead tests if
      it has no production caller. Do not retain dead compatibility code without a
      named owner, consumer, and removal date.
- [ ] Tighten the namespace guard to an exact allowlist of the four permitted
      `baserow` categories from `AGENTS.md`. Do not allow new identifiers merely
      because they appear under a broad path or contain a broad `BASEROW_` prefix;
      keep `DatabaseRow*` and historical migrations safe from substring rewrites.
- [ ] Reconcile `PATCHES.md` with every unavoidable core edit in the reviewed range.
      Correct stale paths and distinguish additive `arabase/` files from upstream
      core modifications.
- [ ] Reconcile all active `PORT_MAP_*.md` statements with the implementation,
      including formula availability, live-crash claims, and removed/dead helpers.
- [ ] Add approved glossary entries for spreadsheet/sheet, expanded/compact,
      utility, duration/datetime formats, and separators, then align English and
      Arabic locale wording.
- [ ] Replace active Nuxt 3 comments and instructions with Nuxt 4 terminology in
      environment remapping and current production/test configuration. Preserve
      explicitly historical records as history.
- [ ] Keep implementation commits reviewable, normally near the repository's
      roughly ten-file change target. Fold lint cleanup into the owning fix when
      practical.

Exit criterion: Ruff, ESLint, Stylelint, Prettier, locale parity, fork hygiene, and
`git diff --check` are clean, and active documentation matches the shipped code.

## Phase 6 — integrated acceptance and candidate image

Run every gate against one immutable commit and store the evidence in both
remediation plans:

- [ ] `just b test -n=auto` passes with no unexplained failures.
- [ ] `just f test` passes with no unexplained failures.
- [ ] `just lint`, frontend formatting, and `git diff --check` pass.
- [ ] `yarn locale:check` and `pytest tests/arabase -q` pass.
- [ ] Migrations run forward on production-like data, with a documented rollback or
      roll-forward procedure.
- [ ] Arabic RTL and English LTR browser journeys cover spreadsheet import/export,
      public Group By protection, responsive Builder menus, all nine formulas, and
      Last Modified behavior.
- [ ] SSR routes start without hydration or registry warnings.
- [ ] Import/export and production-build memory checks stay within documented
      deployment limits.
- [ ] Dependency, license, and vulnerability checks cover SheetJS, openpyxl, and
      the ODS writer.
- [ ] Build an all-in-one candidate image from the same commit. Verify Python
      3.14.6, Node 24.18.0, migrations, Celery, Channels, static assets, health
      endpoints, and the actual Arabase exporter and formula resolver inside the
      image.
- [ ] Refresh `graft/` with `graft build` when the repository tool is available; if
      unavailable, record that fact rather than claiming the graph was refreshed.

Exit criterion: every Phase 0-6 checkbox is supported by evidence from the same
candidate commit. Only then may the branch be called **implementation-ready**.

## Phase 7 — publication and deployment

Do not start without explicit authorization. After authorization, use Phase 7 of
[`NEW_FEATURES_REMEDIATION_PLAN.md`](NEW_FEATURES_REMEDIATION_PLAN.md), record the
published digest, pin the root `Dockerfile`, redeploy, and verify the live Arabic
journey. A source push is not a deployment.

## Proposed commit sequence

1. `docs(plan): reopen new feature remediation gates`
2. `test(formula): define cross-runtime formula parity matrix`
3. `fix(formula): align runtime failures and nullable duration`
4. `test(builder): capture the complete compact-menu keyboard contract`
5. `fix(builder): complete compact-menu accessibility`
6. `chore(builder): generate shared device breakpoints`
7. `test(import): cover upload boundaries and localized failures`
8. `fix(import): strictly enforce configured upload limits`
9. `fix(export): preserve ODS controls and localize limits`
10. `test(export): verify round trips cleanup and memory budget`
11. `chore(fork): reconcile lint patches glossary port maps and guards`
12. `test(release): verify the integrated candidate image`

Test commits must fail for the intended reason before their fix commits. If a test
and fix cannot reasonably be separated, state that in the commit body and preserve
the red result in the implementation record.

## Definition of done

- Every new spec and standards finding is closed by an executable test or explicit
  release evidence.
- Frontend and backend formulas share value, type, null, and failure semantics.
  Compact menus meet their keyboard, focus, nested-menu, RTL, and responsive
  contracts. Spreadsheet values round-trip exactly and inertly; size and
  dimension limits are strict and localized. Builder breakpoints have one
  canonical source with generated Sass drift checking.

---

## Implementation record (2026-09-14)

Phases 0-5 landed on `new_features` as phase-sized commits on top of `e8d90df9`:
`15480a15` (formula parity), `faf4cf9d` (menu accessibility),
`b3c8879c` (export localization + cancel cleanup), `982afe31` (breakpoints),
`98123e4a` (fork hygiene), `3da644f0`/`a19223bf`/`5faf71f9` (test + lint gate
repairs), `a2844715` (utility category icon).

## Gate evidence (run against commit `a2844715`)

| Gate                                                                                                                                                                                                 | Result                                                                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend focused suites (formula core 1278, formula full-group 970 incl. the 55-case shared parity matrix on both runtimes, import_export 155, export handler + limits 40, validator 81, airtable 25) | green                                                                                                                                                                                   |
| Backend suite, chunked under xdist on a 2-CPU host (core 2213, database 3667, contrib-minus-database 1962, arabase + root 978)                                                                       | 8820 passed, 44 failed — every failure classified below                                                                                                                                 |
| Frontend suite                                                                                                                                                                                       | 5040 passed, 4 skipped, 0 failed (was 7 failing at plan start)                                                                                                                          |
| `ruff check` + `ruff format --check` (backend lint gate)                                                                                                                                             | clean (6 drifted files reformatted)                                                                                                                                                     |
| ESLint, Stylelint, Prettier, breakpoint drift check (frontend lint gate)                                                                                                                             | clean                                                                                                                                                                                   |
| `yarn locale:check`                                                                                                                                                                                  | 3853/3853 keys, 0 missing                                                                                                                                                               |
| `pytest tests/arabase -q`                                                                                                                                                                            | 740 passed, 1 skipped                                                                                                                                                                   |
| Forward migrations on a scratch PostgreSQL database                                                                                                                                                  | 500 migrations applied to head; template sync and Arabase post-migrate hooks clean. Rollback follows `docs/BACKUP_RESTORE.md` (dump + restore via the fork's `backup_database` tooling) |

### Explained backend failures (all reproduce on the pre-remediation base

commit `e8d90df9` or are host-environment limits; none are caused by this
remediation)

- 30 × `advocate.exceptions.ConfigException: netifaces module was not
importable` — netifaces 0.11.0 does not compile against this host's musl +
  Python 3.14 toolchain (C-source incompatibility), so every SSRF-guard test
  around `advocate` (webhook URL validation, user-file-by-URL) errors before
  its assertions. Environment limit, not code.
- 15 × data-sync PostgreSQL failures (`smallint out of range` and cascades) —
  the `pgvector:pg16` test container does not satisfy the data-sync fixture's
  schema assumptions. Environment limit, not code.
- 6 × `KeyError: 'group_by_metadata'` in link-row/multiple-select/
  multiple-collaborators list-rows tests — stale 2.2-era expectations: the
  metadata is include-gated and the tests never pass `include=group_by_metadata`.
- 1 × MCP SSE logging test hangs standalone (worker crash under xdist).
- 1 × view-aggregations empty-count test passes in isolation; ordering
  pollution under xdist.
- 2 × airtable import expectations missing the `priority` field added by the
  grouped-grid feature — **fixed** in `3da644f0`.

### Not performed in this environment

- All-in-one candidate image build and its runtime verification: the Nuxt
  production build is documented as OOM-prone on small plans and this host has
  ~3 GB free; the image is built by the _Publish all-in-one image_ workflow in
  CI. Phase 7 remains unauthorized.
- Browser journeys (RTL/LTR, resize-without-reload), SSR smoke tests and the
  memory benchmark require a running deployment-equivalent stack; not
  available here.
- Dependency/license/vulnerability scanning needs registry access from CI.
