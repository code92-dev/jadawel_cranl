# New features remediation plan

Status: **planned**

Source review: `new_features` at `f702ed8e1609e3a2deeeb61cf0a7917453a8a159`

Parent plan: [`NEW_FEATURES_PLAN.md`](NEW_FEATURES_PLAN.md)

## Objective

Close every implementation and standards gap found in the review of the upstream
2.3 feature port, then rerun the original plan's acceptance and deployment gates.
The branch must not be described as implemented until Phases 0-6 below are green.
Production publication and deployment remain a separate, explicitly authorized
Phase 7.

## Repair order

Work in this order so security and broken contracts are fixed before broader UI and
release work:

| Phase | Outcome                                               | Depends on                         |
| ----- | ----------------------------------------------------- | ---------------------------------- |
| 0     | Correct status and capture failing regression tests   | Nothing                            |
| 1     | Protect public data and restore import limits         | Phase 0                            |
| 2     | Complete runtime formulas and null semantics          | Phase 1                            |
| 3     | Make Builder responsiveness and menus accessible      | Phase 2                            |
| 4     | Correct spreadsheet exports and enforce format limits | Phase 1                            |
| 5     | Restore fork, documentation, and scope hygiene        | Phases 2-4                         |
| 6     | Run full cross-feature acceptance and release gates   | Phases 1-5                         |
| 7     | Publish and deploy the image                          | Phase 6 and explicit authorization |

Phases 2, 3, and 4 should remain separate commits. Phase 4 can run in parallel with
Phases 2-3 after Phase 1, but each phase must pass its own focused tests before the
branch moves forward.

## Phase 0 — establish an honest baseline

- [ ] Change the parent plan status from `implemented` to `remediation in progress`
      and replace any completion claim that is contradicted by this document.
- [ ] Record the reviewed commit and the current focused-test results in the parent
      plan's implementation record.
- [ ] Add a failing regression test for each functional issue before changing its
      implementation:
    - saved hidden Group By fields on public row and group-data endpoints;
    - XLSX/ODS importer upload-size enforcement;
    - `duration_format(null(), 'h:mm')` through the real parser/resolver;
    - frontend registration/execution of all nine new formula functions;
    - compact-menu keyboard activation, Escape, and focus restoration;
    - device classification at 420, 421, 500, 501, 767, 768, and 769 pixels;
    - exact round-trip preservation of formula-looking spreadsheet text;
    - workbook row and column limits.
- [ ] Add missing acceptance fixtures from the original Phase 0: multilingual
      workbooks, a five-level grouped table, responsive Builder pages, duration cases,
      and Last Modified row-move cases.

Exit criterion: every finding has a test that fails for the expected reason, and
the documentation no longer declares the incomplete branch finished.

## Phase 1 — public-data protection and import limits

### Public Group By

- [ ] Introduce one helper that resolves the effective public Group By rules for
      both public rows and public group-data endpoints.
- [ ] Apply `visible_field_ids` to saved rules as well as ad-hoc rules. Do not put a
      hidden field's raw value, display value, metadata, or aggregate into a public
      response merely because it is part of the saved view configuration.
- [ ] Define the response after filtering consistently: preserve the remaining
      visible nesting levels; if no levels remain, return the existing ungrouped/empty
      group-data shape.
- [ ] Apply the same rule to public row ordering and `group_by_metadata`, not only
      the new group-data endpoint.
- [ ] Verify visible aggregates and counts remain correct after hidden levels are
      removed.
- [ ] Add tests for anonymous and password-protected public views, hidden-first and
      hidden-middle nesting, all-levels-hidden, explicit hidden parameters, visible
      saved grouping, and public aggregations.

Primary areas:

- `backend/src/jadawel/contrib/database/api/views/grid/views.py`
- `backend/src/jadawel/contrib/database/api/views/utils.py`
- `backend/tests/jadawel/contrib/database/api/views/grid/`

### Spreadsheet import size limit

- [ ] Replace `baserowMaxImportFileSizeMb` with the canonical
      `jadawelMaxImportFileSizeMb` in `TableExcelImporter.vue`.
- [ ] Centralize the CSV/XML/spreadsheet byte-limit calculation in a small shared
      helper so importer names cannot drift again.
- [ ] Treat a missing, non-numeric, zero, or negative runtime value deliberately;
      do not let `NaN` silently disable validation. Use the documented configured
      default unless an explicit supported value says otherwise.
- [ ] Test one file below the limit, exactly at the limit, and one byte above it,
      including the translated error interpolation in English and Arabic.
- [ ] Add a repository check for newly introduced source identifiers using the
      obsolete `baserow` namespace, excluding the four documented exceptions.

Exit criterion: no public response exposes hidden grouping data and all spreadsheet
import paths enforce the same configured limit.

## Phase 2 — complete runtime formulas

### Frontend parity

- [ ] Port frontend implementations for `abs`, `range`, `to_json`, `from_json`,
      `null`, `number_format`, `to_duration`, `duration_format`, and `to_datetime` into
      `web-frontend/modules/core/runtimeFormulaTypes.js`.
- [ ] Register every type in `web-frontend/modules/core/plugin.js` in the same
      deterministic order used by the backend.
- [ ] Port any shared frontend duration parser/formatter and argument types rather
      than duplicating conversion rules inside individual formula classes.
- [ ] Add autocomplete category metadata, signatures, examples, validation/help
      text, and English/Arabic locale keys.
- [ ] Add the same bounded `range` maximum to browser and backend configuration;
      propagate its environment setting through the normal Django/Nuxt configuration
      paths if it is configurable.
- [ ] Remove the “frontend entirely unported” state from
      `docs/PORT_MAP_FORMULAS.md` only after parity tests pass.

### Duration null contract

- [ ] Make nullability explicit for the first `duration_format` argument. Prefer a
      per-argument or per-function nullable contract; do not weaken duration validation
      globally.
- [ ] Ensure validation and execution follow the same rule, including the real
      parser path used by Builder formulas.
- [ ] Replace the direct `execute({}, [None, ...])` test with parser/resolver tests,
      while retaining unit coverage for argument validation.
- [ ] Cover null, empty string, invalid duration, negative and fractional duration,
      invalid format, and nested expressions in both runtimes.

### Parity gate

- [ ] Build a shared expression matrix and assert compatible backend/frontend typed
      results and compatible failures for every new function.
- [ ] Exercise the functions through Builder and Automation formula inputs so the
      test covers registration, autocomplete, parsing, preview, serialization, and
      backend execution—not only class-level methods.

Exit criterion: all nine functions are discoverable and executable in the browser,
and the parity matrix passes for values, types, limits, nulls, and errors.

## Phase 3 — responsive and accessible Builder UI

### One breakpoint contract

- [ ] Choose one canonical desktop/tablet/smartphone boundary model and export it
      from a single source rather than maintaining unrelated JS and SCSS numbers.
- [ ] Update `deviceTypes.js`, `PageContent.vue`, and column/menu media queries to
      use non-overlapping intervals. Pay particular attention to 421-500px and the
      shared 768px edge.
- [ ] Confirm editor device selection, preview state, published rendering, column
      stacking, and menu variants resolve to the same device at every boundary.
- [ ] Add component tests at each boundary plus a browser test that resizes a
      published page without reloading it.

### Accessible compact menus

- [ ] Render trigger and close actions as semantic buttons, or give the shared icon
      control equivalent role, focusability, keyboard activation, and accessible name.
      Avoid changing every `ABIcon` consumer unless its public contract is deliberately
      upgraded and regression-tested.
- [ ] Add `aria-expanded`, `aria-controls`, and suitable menu/dialog labelling.
- [ ] On open, move focus into the compact panel. Keep keyboard focus within it
      while open when it behaves as an overlay.
- [ ] Close on Escape and click-outside, then restore focus to the original trigger.
- [ ] Make nested submenu controls operable with Enter/Space and expose their
      expanded state.
- [ ] Preserve edit-mode preview locking and ensure unmount/device changes do not
      leave focus, listeners, or lock state behind.
- [ ] Test keyboard-only behavior, focus order, nested items, empty menus, RTL/LTR,
      edit mode, public mode, and device transitions.

Exit criterion: JavaScript and CSS agree at all viewport boundaries, and the compact
menu passes automated component checks plus a manual keyboard journey in Arabic RTL
and English LTR.

## Phase 4 — spreadsheet export correctness and limits

### Preserve text without formula execution

- [ ] Remove the stored apostrophe mutation from `_spreadsheet_text`.
- [ ] Keep XLSX cells explicitly typed as strings and ODS cells written with
      `office:value-type="string"`; confirm Excel and LibreOffice do not execute values
      beginning with `=`, `+`, `-`, `@`, `|`, `%`, tab, CR, or LF.
- [ ] If an application still interprets a string cell as executable, use a
      format-level protection that does not alter the cell's logical value, and document
      the verified behavior.
- [ ] Test stored value, displayed value, and import round trip for every dangerous
      prefix, including Arabic text and leading whitespace.

### Dimension and resource limits

- [ ] Define named XLSX and ODS row/column limits, including whether a header row
      consumes one row.
- [ ] Validate field count before starting a job and stop row generation at a clear
      boundary with an actionable, translated error. Never emit a silently truncated
      workbook.
- [ ] Test exact-limit and one-over-limit row/column cases without constructing a
      million-row fixture; isolate the counter/validator so boundary tests remain fast.
- [ ] Verify cancellation cleans temporary files and that failure does not leave a
      downloadable partial workbook.
- [ ] Repeat the representative memory benchmark for both formats after the change.

Exit criterion: formula-looking values round-trip unchanged and inert, oversized
exports fail predictably, and normal exports retain streaming memory behavior.

## Phase 5 — fork and documentation hygiene

### Additive exporter placement

- [ ] Move the new Jadawel-specific XLSX/ODS exporter implementation under
      `backend/src/arabase/` and register it in `ArabaseConfig.ready()` through the
      existing table-exporter registry.
- [ ] Keep only genuinely shared upstream changes in `jadawel/`. If serializers or
      API contracts cannot move cleanly, document the exact seam and smallest remaining
      core edit in `PATCHES.md`.
- [ ] Update imports and tests so no accidental duplicate registration occurs.
- [ ] Audit the unused `ServiceFile` subsystem introduced with the formula work;
      remove it and its dependencies if no shipped formula or integration calls it, or
      document and test the planned caller if it is intentionally retained.

### Documentation and source hygiene

- [ ] Update `README.md`, `AGENTS.md`, configuration comments, and active developer
      docs from Nuxt 3 to Nuxt 4. Preserve genuinely historical references.
- [ ] Follow the repository's agent-documentation workflow for `AGENTS.md`.
- [ ] Add a dedicated Nuxt 4 entry and complete core-file inventory to `PATCHES.md`.
- [ ] Add approved Arabic glossary entries for spreadsheet/sheet,
      expanded/compact, and any other recurring terms introduced by these features;
      then align locale wording with the glossary.
- [ ] Remove the trailing blank line reported by `git diff --check` in
      `backend/src/jadawel/contrib/database/views/handler.py`.
- [ ] Reconcile every `PORT_MAP_*.md` status with the actual implementation.

Exit criterion: new fork-owned behavior lives behind additive seams where possible,
all unavoidable core edits are inventoried, and active documentation describes the
runtime that is actually shipped.

## Phase 6 — full acceptance and release gate

Run focused tests after each commit, then run all of the following on the integrated
branch:

- [ ] Full backend suite: `just b test -n=auto`.
- [ ] Full frontend suite: `just f test`.
- [ ] Backend/frontend lint and formatting: `just lint` and `git diff --check`.
- [ ] Arabic locale parity: `yarn locale:check` from `web-frontend/`.
- [ ] Fork hygiene: `pytest tests/arabase -q` from `backend/`.
- [ ] Migration forward test on production-like data and a documented rollback or
      roll-forward strategy.
- [ ] Browser journeys in Arabic RTL and English LTR for:
    - XLS/XLSX/ODS import and XLSX/ODS export;
    - public five-level grouping with hidden fields and aggregates;
    - responsive columns and keyboard-only compact menus;
    - all nine formulas in preview and backend execution;
    - row moves preserving `updated_on` and Last Modified formulas.
- [ ] SSR smoke tests for login, workspace/table, public view, Builder preview, and
      Arabase routes with no hydration or registry warnings.
- [ ] Memory tests for large import/export, grouped scrolling, Django/Celery, and
      the Nuxt production build using deployment-equivalent limits.
- [ ] Dependency/license and vulnerability checks for SheetJS, openpyxl, and the
      hand-written ODS package output.
- [ ] Build an all-in-one candidate image and verify Python 3.14.6, Node 24.18.0,
      migrations, Celery, Channels, static assets, and health endpoints locally.
- [ ] Refresh `graft/` with `graft build` when the tool is available.

Exit criterion: every original acceptance criterion and every regression in this
plan passes on one candidate image. At this point the branch may be called
**implementation-ready**, but not deployed.

## Phase 7 — authorized publication and CranL deployment

Do not start this phase without explicit authorization.

- [ ] Run the **Publish all-in-one image** workflow for the reviewed commit.
- [ ] Record the immutable published digest and verify its architecture and labels.
- [ ] Bump `ARG JADAWEL_IMAGE` in the root `Dockerfile` to that digest.
- [ ] Redeploy using `docs/DEPLOY_CRANL.md`; a source push is not a deployment.
- [ ] Verify live migrations, version/digest, health, cache behavior, static assets,
      and one real Arabic user journey.
- [ ] Update both plan documents to `completed and deployed`, including commit,
      digest, deployment date, and verification evidence.

## Proposed commit sequence

1. `test(features): capture remediation regressions`
2. `fix(database): protect hidden public group data`
3. `fix(import): enforce spreadsheet upload limits`
4. `fix(formula): propagate null durations through parsing`
5. `feat(formula): complete frontend runtime formula support`
6. `fix(builder): unify responsive device boundaries`
7. `fix(builder): make compact menus keyboard accessible`
8. `fix(export): preserve inert spreadsheet text exactly`
9. `fix(export): enforce workbook dimension limits`
10. `refactor(export): register spreadsheet exporters additively`
11. `chore(fork): reconcile patches glossary and Nuxt docs`
12. `test(release): verify new feature integration`

The first commit may contain only tests and documentation. Subsequent commits should
turn their corresponding tests green without weakening assertions. Keep generated
lockfile changes with the feature that requires them.

## Definition of done

- Every checkbox in Phases 0-6 is complete.
- No public endpoint exposes a hidden field through grouping, metadata, ordering,
  aggregation, or display values.
- Spreadsheet imports enforce configured limits and exports preserve values while
  remaining inert and within format/resource limits.
- All nine formulas have frontend/backend parity, including real-parser null
  propagation and bounded range generation.
- Builder device selection matches rendered CSS and compact menus are fully usable
  without a pointer in Arabic and English.
- Full CI, locale parity, fork hygiene, migrations, browser journeys, memory checks,
  and the candidate image pass.
- Phase 7 is complete before any documentation claims the feature set is deployed.
