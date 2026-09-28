# Dashboard widgets plan — charts + three Jadawel widgets

## Status (2026-08-03)

| Phase | State |
|---|---|
| A — grouped aggregation service | **Implemented and tested** |
| B — chart widget backend | **Implemented and tested** |
| C — chart widget frontend | **Implemented and tested** (4 variations, settings form, RTL, en+ar; 10 unit tests) |
| D1 — records list widget | **Implemented and tested** |
| D2 — progress widget | **Implemented and tested** |
| D3 — upcoming dates widget | **Implemented and tested** |
| Text widget (optional freebie) | **Implemented** in the dashboard redesign |

The 2026-09-28 redesign (`docs/DASHBOARD_REDESIGN.md`) redrew all of these
widgets, moved the board to 12 columns, and added the text widget, the
horizontal bar and area charts, and the progress gauge.

Verified so far:

- `makemigrations --check --dry-run arabase` → *No changes detected* (migration
  0001 was hand-written and this is what confirms it matches the models; 0002 was
  generated)
- `pytest backend/tests/arabase` → **53 passed**
- `vitest test/unit/arabase` → **36 passed** across four specs
- `ruff check` / `ruff format --check` on the new code → clean
- `prettier --check` and `stylelint` on `modules/arabase` → clean
- `check-locale-parity.mjs --strict` → 3573/3573

The frontend test earned its keep immediately: it caught `ChartWidget` treating
the `colors.module.scss` import as a plain lookup table. A CSS modules object can
return a *generated class name* for a key it does not export, so an unknown colour
name silently became a bogus colour instead of falling back to the palette. Colour
resolution now only accepts a value that actually looks like one.

Not verified:

- ESLint could not be run locally (it needs a generated `.nuxt/eslint.config.mjs`);
  prettier and stylelint were run in its place. The production build in the
  publish workflow is the backstop that compiles every template.
- The five failures in `tests/jadawel/contrib/dashboard/api/` are **pre-existing**
  — confirmed by running them at the parent commit. They assert English DRF error
  strings that come back in Arabic because the fork defaults `LANGUAGE_CODE` to
  `ar`.

Answers taken for the three open questions at the bottom: the API accepts up to
5 series and the settings UI offers 3; the bucket cap is 100 (`ARABASE_CHART_MAX_BUCKETS`);
no locked tiles are shown.

### Where the code landed

| Piece | Path |
|---|---|
| Grouped aggregation models / service type / serializers | `backend/src/arabase/integrations/local_jadawel/` |
| Upcoming-rows service | `backend/src/arabase/integrations/local_jadawel/upcoming_rows.py` |
| All four widget models + types | `backend/src/arabase/dashboard/widgets/` (`base.py` holds what they share) |
| Migrations | `backend/src/arabase/migrations/` (`0001` charts, `0002` phase D) |
| Registry hooks | `backend/src/arabase/apps.py` |
| Backend tests | `backend/tests/arabase/test_*.py` |
| Frontend widget types / components / settings / forms | `web-frontend/modules/arabase/dashboard/` |
| Frontend service type | `web-frontend/modules/arabase/integrations/serviceTypes.js` |
| Registry plugin, locales, tile SVGs, SCSS | `web-frontend/modules/arabase/` |

### Deviations from the plan as written below

1. **No "other" bucket.** Buckets past the cap are dropped after sorting and the
   dispatch result carries `truncated: true`, which the widget surfaces as a
   badge. Rolling the tail into an "other" bucket needs a second query for a
   marginal gain; deferred.
2. **Default sort is the first series descending** when no sort is configured.
   This is what makes the cap safe — without an ordering, a table with more
   distinct values than the cap would show an arbitrary subset.
3. **Sorts are modelled and honoured but have no UI yet.** The API accepts
   `aggregation_sorts`; the settings panel does not expose them.
4. **The grouped service is not offered in the application builder's data source
   picker.** Its frontend type extends `LocalJadawelTableServiceType` rather than
   the data-source mixin, because its only form is dashboard-shaped. Exposing it
   to the builder is a follow-up.
5. **`series_config` supports `color` and `label` only** (no per-series chart type
   for combo charts), and the settings panel does not edit it yet — the chart
   falls back to the palette and the field name.
6. **Rich field values render as text** in the two list widgets. A single select
   prints its label, link rows and collaborators print a comma-joined list. Using
   the grid's field components instead would drag editing, selection and row
   context into a read-only list.
7. **`local_jadawel_upcoming_rows` is hidden from the application builder's data
   source picker** (`isDataSource` returns false). It inherits the list-rows form,
   which has no date-field control, so a builder user could otherwise create one
   that can never dispatch.

## Goal

The dashboard's "Add new widget" picker currently offers only **Summary**. The
Bar, Line, Pie and Doughnut tiles shown locked in upstream Jadawel are one
premium widget type (`chart`) presented as four *variations* — and this fork
removed `premium/` entirely, so they don't exist here in any form.

This plan implements them natively in Jadawel, plus three new widgets that fit
how Jadawel is actually used (Arabic-first business dashboards):

1. **Chart widget** — bar / line / pie / doughnut (parity with upstream premium)
2. **Records list widget** — latest N rows from a table/view ("أحدث السجلات")
3. **Progress widget** — aggregate vs. a target, as a percent bar/ring
4. **Upcoming dates widget** — agenda of rows whose date field falls in the next N days

## What exists today (verified in this tree)

| Piece | Where | State |
|---|---|---|
| Polymorphic `Widget` base + registry | `backend/src/jadawel/contrib/dashboard/widgets/models.py`, `registries.py` | Open registry; `SummaryWidget` is the only registration (`contrib/dashboard/apps.py:72`) |
| Widget CRUD API | `contrib/dashboard/api/widgets/` | Registry-driven, polymorphic — new types need **no new endpoints** |
| Data sources + dispatch | `contrib/dashboard/data_sources/`, frontend `store/dashboardApplication.js` (`dispatchDataSource`) | Generic; any service type wrapped in a data source flows through it |
| Aggregation service | `LocalJadawelAggregateRowsUserServiceType` (`contrib/integrations/local_jadawel/service_types.py:1184`) | Single value, **no grouping** — fine for Summary/Progress, insufficient for charts |
| Row-listing service | `LocalJadawelListRowsUserServiceType` | Exists — Records list and Upcoming dates reuse it as-is |
| Frontend widget registry | `web-frontend/modules/dashboard/widgetTypes.js` | `WidgetType.variations` getter already supports the one-type-many-tiles picker UX |
| Chart rendering | `chart.js 3.9.1`, `chartjs-adapter-moment`, `vue-chartjs 5.3.3` in `web-frontend/package.json` | **Already dependencies** (admin dashboard uses them) — zero new packages |
| Fork-specific app | `backend/src/arabase/`, `web-frontend/modules/arabase/` | Exists, currently has no models/migrations |

The only genuinely new machinery is a **grouped aggregation service**:
"group rows by field X (or date bucket), compute aggregation(s) per group."
Everything else is assembly.

## Design decisions

**D1 — New backend code lives in `arabase`, not `contrib/dashboard`.**
New models mean migrations. Upstream keeps adding migrations to
`contrib.dashboard`; fork migrations interleaved there collide on every
upstream merge. `arabase` is fork-owned, so its migration sequence is safe.
Widget models FK to `dashboard.Dashboard` across apps without issue.

**D2 — Keep upstream premium's public type names.**
Widget type `chart`, service type `local_jadawel_grouped_aggregate_rows`.
Template/export files reference registry type strings, not app labels — using
upstream's names means upstream dashboard templates containing charts import
instead of being skipped by `sync_templates` (the same skip mechanism we see
today for kanban/timeline views), and our own exports stay portable.

**D3 — One `chart` widget type, four variations.**
Matches upstream UX and the picker's existing `variations` support. The
variation only presets `default_chart_type` on creation; users can switch chart
type in settings afterwards.

**D4 — RTL and Arabic are first-class, not afterthoughts.**
Chart.js supports `rtl: true` and `textDirection` per chart — wire both to the
active locale. Numbers/dates format through the app's existing i18n. Every new
string lands in `en.json` **and** `ar.json` in the same commit: the strict
locale-parity CI gate (`yarn locale:check`) fails the build otherwise.

**D5 — Implementation happens in `Azizahmed/Jadawel`.**
Per `docs/DEPLOY_CRANL.md`: feature work belongs in the main repo, then merges
into `jadawel_cranl`, then a new image is published and pinned. Committing
features straight to the deployment repo diverges the trees.

---

## Phase A — grouped aggregation service (backend)

The foundation; charts are unusable without it.

New in `backend/src/arabase/integrations/` (registered into the existing
`service_type_registry`):

**Models**
- `LocalJadawelGroupedAggregateRows(LocalJadawelViewService)` — table/view ref,
  filters (reuse `LocalJadawelTableServiceFilterableMixin`)
- `LocalJadawelTableServiceAggregationSeries` — FK to service, `field`,
  `aggregation_type`, `order` (start with the aggregation types the existing
  service supports; same `unsupported_aggregation_types` exclusion)
- `LocalJadawelTableServiceAggregationGroupBy` — FK to service, `field`
  (nullable ⇒ no grouping = single-bucket chart). v1: **one** group-by;
  the model still holds them as a list for forward compatibility.
- `LocalJadawelTableServiceAggregationSortBy` — sort on group label or series
  value, asc/desc

**Service type** `local_jadawel_grouped_aggregate_rows`
- `dispatch_data`: build the table model queryset, apply view/service filters,
  `.values(group_field).annotate(...)` one annotation per series; cap at
  `ARABASE_CHART_MAX_BUCKETS` (default 100, largest-N-plus-"other" beyond it)
- Group-by on single select resolves option labels (and colors — the frontend
  can color pie slices with the select option colors); on date/datetime fields
  v1 groups by day (date bucketing granularity is a v2 setting)
- `generate_schema` / `get_context_data` following the existing aggregate
  service's pattern
- Export/import serialization (`SerializedDict`, field/id remapping in
  `deserialize_property`) so template import and workspace duplication work

**Tests** `backend/tests/arabase/` (keeps the fork-hygiene suite location):
dispatch with/without grouping, per-aggregation-type results, filters, trashed
field/view handling, export/import round-trip, permission checks via the data
source (already enforced by the dashboard layer).

Estimate: **3–4 days**.

## Phase B — chart widget (backend)

- `ChartWidget(Widget)` in `arabase`: `data_source` FK (PROTECT, mirroring
  `SummaryWidget`), `default_chart_type` (`bar|line|pie|doughnut`),
  `series_config` JSON (per-series color/label overrides)
- `ChartWidgetType(WidgetType)` — clone the `SummaryWidgetType` lifecycle
  (auto-create data source on create, trash/restore/delete cascade,
  serialize/deserialize `data_source_id`), but create the data source with the
  grouped service type
- Register in `arabase/apps.py`; one `arabase` migration
- Tests: CRUD via the widget API, duplication, trash/restore, export/import

Estimate: **1–2 days**.

## Phase C — chart widget (frontend)

New under `web-frontend/modules/arabase/dashboard/` (registered from
`modules/arabase/plugin.js` into the `dashboardWidget` registry):

- `ChartWidgetType` with `variations` returning the four tiles (bar / line /
  pie / doughnut), each passing `default_chart_type` in `params`; four SVG tile
  images matching `summary_widget.svg`'s style
- `ChartWidget.vue` — header/context-menu/misconfigured-badge structure copied
  from `SummaryWidget.vue`; body renders via `vue-chartjs` (`Bar`, `Line`,
  `Pie`, `Doughnut`), `rtl` + `textDirection` from the active locale,
  `maintainAspectRatio: false` so it fills the widget frame
- `ChartWidgetSettings.vue` + `GroupedAggregateRowsDataSourceForm.vue`
  (pattern: `AggregateRowsDataSourceForm.vue`): table/view picker, group-by
  field picker, series editor (field + aggregation, add/remove), chart-type
  switcher, per-series color override
- Colors: default palette from select-option colors when grouping by single
  select, otherwise the app palette
- Locales: `en.json` + `ar.json` together (D4)
- Tests per the `write-frontend-unit-test` skill: widget renders from mocked
  dispatch data; settings form emits correct updates; empty/misconfigured states

Estimate: **4–5 days**. Charts total: **~2 weeks** including review slack.

## Phase D — the three Jadawel widgets

All three are implemented. What was built, and where it departed from the sketch:

### D1. Records list widget (`records_list`)
The latest rows of a table or view. Reuses `local_jadawel_list_rows` unchanged.
The row limit is the **service's** `default_result_count` rather than a widget
field as originally planned — duplicating a limit that the service already owns
would have meant two places to keep in step. The widget stores `field_ids`
(remapped on import), and with none stored it shows the table's first three
fields so a new widget is never a blank frame.

### D2. Progress widget (`progress`)
An aggregation over a target, as a bar or a ring, coloured by two thresholds.
Reuses the existing ungrouped `local_jadawel_aggregate_rows`, and reuses
upstream's `AggregateRowsDataSourceForm` verbatim for the data half of its
settings. Overshooting the target reads as ">100%" in the number but the bar
stops at full, because a fill wider than its track escapes the widget.

### D3. Upcoming dates widget (`upcoming_dates`)
An agenda of rows due within 7/14/30 days, soonest first, overdue flagged and
counted in the header. This needed the one new service in Phase D —
`local_jadawel_upcoming_rows`, a subclass of the list-rows service adding
`date_field`, `days_ahead` and `include_overdue`. The alternative considered was a
relative-date *service filter*, which was rejected: those filter values are an
encoded string (timezone, amount, unit) that a widget settings panel has no
business assembling. Filtering in the browser was never an option — it would mean
fetching every row.

Notes on the window: datetime fields are compared by their **date part**, since a
timestamp compared against a date includes or drops a whole day at the boundary
depending on the time. The date ordering deliberately replaces any view or service
sort (an agenda not in date order is not an agenda) while filters still apply, so
a view filter can scope the agenda to one assignee. `created_on` and
`last_modified` are accepted as date fields, not just the `date` type. Hijri
display remains out of scope.

**Hijri display is still explicitly deferred** — it touches date formatting
globally, not just this widget.

A plain **Text/heading widget** (title + markdown body, no data source) remains
the cheap freebie it was: about half a day, not yet built.

## Rollout

1. Branch from the feature repo's mainline in `Azizahmed/Jadawel` (D5); ship
   phases as separate PRs (A+B together, C, then D widgets individually)
2. Gates per PR: `just b test`, `just f test`, `yarn locale:check`, `just lint`
3. Merge into `jadawel_cranl` `main` → run **Publish all-in-one image** with a
   new tag → bump `ARG JADAWEL_IMAGE` in the root `Dockerfile` → Deploy on
   CranL (per `cranl_fix.md` runbook)
4. After charts ship: re-run `sync_templates` — upstream templates whose
   dashboards contain chart widgets will import them instead of skipping (D2
   naming decision is what makes this work)

## Order and effort summary

| # | Deliverable | Effort | Depends on |
|---|---|---|---|
| A | Grouped aggregation service | 3–4 d | — |
| B | Chart widget backend | 1–2 d | A |
| C | Chart widget frontend (4 variations) | 4–5 d | B |
| D1 | Records list widget | 2–3 d | patterns from B/C |
| D2 | Progress widget | 2 d | patterns from B/C |
| D3 | Upcoming dates widget | 3 d | patterns from B/C |
| — | Text widget (optional freebie) | 0.5 d | — |

Total: roughly **3 weeks** of focused work for everything; the four chart
widgets alone are **~2 weeks** and remove the biggest visible gap with
upstream's paid tier.

## Open questions (decide before Phase A starts)

1. Multiple series in v1, or single series with the model shaped for more?
   (Recommendation: model supports N, settings UI allows up to 3.)
2. Cap `ARABASE_CHART_MAX_BUCKETS` at 100 with "other" bucket — acceptable?
3. Should the picker keep showing locked tiles for anything? (Recommendation:
   no — in a fork with no paid tier, locked tiles are noise.)
