# PATCHES.md — Core-file edits log

This file tracks every edit we make to **upstream-derived core files** (i.e. files
that also exist upstream, outside our additive `backend/src/arabase/` and
`web-frontend/modules/arabase/` code). Each entry records the file and the reason.

Additive files we create (e.g. under `arabase/`, `docs/`, new CI workflows) are **not**
logged here — only modifications to files that came from upstream.

Since the `jadawel` rename (2026-08-06) this log is a **provenance record**, not a
merge-cost ledger. There is no `upstream` remote, and the rename moved 2,214 files
past git's rename-detection limit, so an upstream merge is no longer the plan. The
question the log still answers is "did we author this, or inherit it?", which is what
decides how an upstream CVE gets applied. **Merge risk** columns in older entries are
kept as written for the historical record.

## Theme-colored interface chrome (2026-09-14–15)

| File                                                                                                                                                                 | Change                                                                                                         | Reason                                                                                                | Merge risk |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/core/assets/scss/components/views/grid.scss`                                                                                                   | Grid column headers use the active interface theme's header and border CSS custom properties                   | Prevent fixed sage palette values from covering the selected theme on every table's column row        | low        |
| `web-frontend/modules/core/assets/scss/{abstracts/_button.scss,components/header.scss,components/app_utilities.scss,components/automation/automation_workflow.scss}` | Primary buttons and content-header controls use the active primary palette, with readable white foregrounds    | Apply the selected interface color consistently to the table, builder, and automation chrome          | low        |
| `web-frontend/modules/core/assets/scss/components/{dashboard.scss,sidebar.scss}`                                                                                     | Keep workspace-home content white while coloring the workspace selector and popup avatars with the primary hue | Separate the neutral home surface from the themed application chrome without losing the chosen accent | low        |
| `web-frontend/modules/database/components/view/ShareViewLink.vue`                                                                                                    | Remove the shared-state primary background class from the share control                                        | Avoid a second highlighted block inside the already-solid themed header                               | low        |

**Test:** `web-frontend/test/unit/core/gridHeaderTheme.spec.js`.

## Upstream 2.3 port — runtime, cache and row-move semantics (2026-09-13)

**Context:** Phase 1 of `docs/NEW_FEATURES_PLAN.md` ports three upstream Baserow 2.3
OSS changes into the fork. Two are one-line semantic changes, so they are recorded
here rather than in an `arabase/` module; the Python image bumps are deploy files.

| File                                                                          | Change                                                                          | Reason                                                                                                       | Merge risk            |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------- |
| `backend/Dockerfile`, `deploy/all-in-one/Dockerfile`, `embeddings/Dockerfile` | `python:3.14.3-slim-trixie` → `python:3.14.6-slim-trixie`                       | Upstream 2.3 fixed a backend memory leak by moving to 3.14.6                                                 | none (image tag only) |
| `backend/src/jadawel/config/settings/base.py`                                 | `JADAWEL_CACHE_TTL_SECONDS` default `0` → `120`                                 | Match upstream 2.3, which enables the general object cache by default. `0` remains the documented opt-out    | low                   |
| `backend/src/jadawel/contrib/database/rows/handler.py`                        | `move_row` persists `order` only, no longer `order` and `updated_on`            | Upstream 2.3 breaking change: moving a row must not make Last Modified fields appear changed                 | medium                |
| `backend/src/jadawel/contrib/database/fields/field_types.py`                  | `CreatedOnLastModifiedBaseFieldType.include_in_row_move_updated_fields = False` | Without it a row move recomputes `created_on`/`last_modified` columns, re-introducing the false modification | low                   |

`move_row` still recalculates every field that can be order-dependent: the loop over
`model._field_objects` and `update_dependencies_of_rows_updated` are untouched, so
lookup and link-row values still refresh while the timestamp columns stay. Permission
checks, `before_rows_update`/`rows_updated` signals, webhooks and realtime propagation
are unchanged.

**Tests:** `backend/tests/jadawel/contrib/database/rows/test_rows_handler.py::test_move_row_does_not_update_last_modified`,
`backend/tests/jadawel/core/test_settings_cache.py`.

## Upstream 2.3 port — runtime formulas and duration (2026-09-13)

**Context:** Phase 3 of `docs/NEW_FEATURES_PLAN.md`. The runtime expression set and
the duration engine it builds on. Ported by a reviewed three-way merge of upstream
2.2.2 and 2.3.3 against the fork; the fork's copies were mechanical renames of 2.2.2,
so the merge was clean apart from `files` merged whole that also carried unrelated
2.3 features (stripped).

| File                                                            | Change                                                                                                                                                                | Reason                                                                 | Merge risk                                                  |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| `backend/src/jadawel/core/duration.py`                          | New: duration token parse/format engine                                                                                                                               | Shared by the runtime functions, the duration field and the validator  | low (new file)                                              |
| `backend/src/jadawel/core/formula/service_file.py`              | New: normalised file value for service formulas — **REMOVED 2026-09-15** in commit `98123e4a`: it had no production consumer (upstream's consumer is enterprise-only) | Historical port row; see the follow-up remediation section below       | low (file deleted)                                          |
| `backend/src/jadawel/core/formula/runtime_formula_types.py`     | Adds abs, range, to_json, from_json, null, number_format, to_duration, duration_format, to_datetime; timedelta-aware arithmetic                                       | Upstream 2.3 rendering formula additions                               | medium                                                      |
| `backend/src/jadawel/core/formula/argument_types.py`            | Adds duration, timedelta, datetime-format, duration-format and separator argument types with `get_error_message`                                                      | Lets a bad argument report the values that are valid                   | low                                                         |
| `backend/src/jadawel/core/formula/registries.py`                | `validate_type_of_args` returns `(index, arg)` pairs                                                                                                                  | So the registry can raise the argument type's own message              | medium (contract change; no other implementors in the tree) |
| `backend/src/jadawel/core/formula/validator.py`                 | `ensure_duration`, `ensure_deserialized_json`, `ensure_json_serializable`, timedelta-aware JSON encoder                                                               | Support the functions above                                            | low                                                         |
| `backend/src/jadawel/core/formula/field.py`                     | Copy before minifying                                                                                                                                                 | A second `get_prep_value` call could blank an already-minified formula | low                                                         |
| `backend/src/jadawel/core/formula/utils/date.py`                | `is_valid_datetime_format`                                                                                                                                            | Used by the new argument type                                          | low                                                         |
| `backend/src/jadawel/contrib/database/fields/utils/duration.py` | Duration parsing used by the field                                                                                                                                    | Shared with the new engine                                             | low                                                         |
| `backend/src/jadawel/config/settings/base.py`                   | New `FORMULA_RANGE_MAX_ITEMS` (default 10000)                                                                                                                         | `range()` must not be able to allocate an unbounded list               | low                                                         |
| `backend/src/jadawel/core/apps.py`                              | Registers the nine new runtime functions                                                                                                                              | Registration site                                                      | low                                                         |

**Tests:** `backend/tests/jadawel/core/test_duration.py` and
`backend/tests/jadawel/core/formula/` (ported from upstream) — 1323 passed.

## Upstream 2.3 port — spreadsheet export (2026-09-13)

**Context:** Phase 4 of `docs/NEW_FEATURES_PLAN.md`. Export is additive: no upstream
exporter covers XLSX or ODS in core, so the fork supplies one. The shared export
plumbing changes below come from upstream 2.3 and are shared with CSV.

| File                                                                                                       | Change                                                                                                                                  | Reason                                                                                                                                                                   | Merge risk |
| ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `backend/src/jadawel/contrib/database/export/file_writer.py`                                               | `QuerysetSerializer` gains `include_row_id` and `include_primary_field`                                                                 | Upstream 2.3 makes the Row ID and primary field columns optional in an export                                                                                            | low        |
| `backend/src/jadawel/contrib/database/export/handler.py`                                                   | Passes those two options through to the serializer                                                                                      | Same                                                                                                                                                                     | low        |
| `backend/src/jadawel/contrib/database/api/export/serializers.py`                                           | Adds `include_row_id` / `include_primary_field` and the XLSX/ODS option serializers                                                     | Same                                                                                                                                                                     | low        |
| `backend/src/jadawel/contrib/database/export/table_exporters/csv_table_exporter.py`                        | `CsvQuerysetSerializer.__init__` forwards `**kwargs`                                                                                    | **Fixes an upstream 2.3 omission**: upstream added the options to the base but left the CSV subclass overriding them, so any CSV export that set them raised `TypeError` | low        |
| — (originally `backend/src/jadawel/contrib/database/apps.py`)                                              | Registration moved out of core `apps.py`: the XLSX/ODS exporters now register additively in `ArabaseConfig.ready()` (commit `2a94b601`) | Fork hygiene: the exporters are fork-owned code under `arabase/export/`, so no core edit is needed for registration                                                      | low        |
| — (originally `backend/src/jadawel/contrib/database/export/table_exporters/spreadsheet_table_exporter.py`) | Implementation moved to `backend/src/arabase/export/spreadsheet_table_exporter.py` (additive)                                           | Same fork-hygiene move; the core path no longer exists                                                                                                                   | low        |
| `backend/src/jadawel/contrib/database/migrations/0212_fileimportjob_importer_type_and_more.py`             | New: adds the two file-import metadata columns                                                                                          | Ported from upstream 0210, re-pointed at the fork's database head                                                                                                        | low        |

Cells whose text begins with `=`, `+`, `-`, `@`, `|`, `%`, tab, CR or LF are written
as text, so opening a downloaded workbook cannot execute user data (CWE-1236). No new
Python dependency was added: `openpyxl` was already present for XLSX, and ODS is
written with the standard library because `odfpy` measured 1233 MB / 583 s for
200,000 rows against the export worker's 768 MB limit (streaming writer: 354 MB / 4.4 s).

**Tests:** `backend/tests/jadawel/contrib/database/import_export/` — 47 passed.

## Upstream 2.3 port — enhanced Group By (2026-09-13)

**Context:** Phase 5 of `docs/NEW_FEATURES_PLAN.md`. Sorting and grouping gain an
explicit order, a view can group by five fields, and a grouped grid fetches its
groups separately from its rows.

| File                                                                                                      | Change                                                                              | Reason                                                           | Merge risk      |
| --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- | --------------- |
| `backend/src/jadawel/contrib/database/views/models.py`                                                    | `ViewSort`/`ViewGroupBy` gain `priority` and are ordered by it                      | Stable, user-controllable ordering                               | medium          |
| `backend/src/jadawel/contrib/database/views/handler.py`                                                   | Priority-chain helpers and the group-by data engine                                 | The feature                                                      | high            |
| `backend/src/jadawel/contrib/database/views/{actions,operations,signals,exceptions,view_aggregations}.py` | Prioritize actions, signal and error types; filtered distinct count                 | Supporting the above                                             | low             |
| `backend/src/jadawel/contrib/database/views/constants.py`                                                 | New                                                                                 | `GROUP_BY_DATA_DEFAULT_LIMIT`                                    | low (new file)  |
| `backend/src/jadawel/contrib/database/api/views/**`                                                       | Group-by data endpoints, serializers, URLs and response assembly                    | The feature                                                      | medium          |
| `backend/src/jadawel/contrib/database/fields/{registries,field_types}.py`                                 | `get_group_by_order`, `get_group_by_display_values`; M2M groups key on their id set | Group values match the row API's shape and are order-insensitive | medium          |
| `backend/src/jadawel/contrib/database/ws/views/signals.py`, `airtable/registry.py`                        | Realtime announce a reordered chain; carry priority on import                       | Supporting                                                       | low             |
| `backend/src/jadawel/contrib/database/migrations/0213_viewgroupby_viewsort_priority.py`                   | New                                                                                 | Ported from upstream 0211, re-pointed at the fork's head         | low             |
| `web-frontend/modules/database/store/view/grid.js`                                                        | Grouped data model, collapse state, absolute-offset placement                       | The feature                                                      | high            |
| `web-frontend/modules/database/utils/{gridGroupBy,gridGroupByRender,rowLifecycle}.js`                     | New                                                                                 | Grouped model and layout maths                                   | low (new files) |
| `web-frontend/modules/database/components/view/grid/**`                                                   | New group-by banner/rows/value components; grid components updated                  | The feature                                                      | medium          |
| `web-frontend/modules/database/components/view/{ViewGroupByContext,ViewSortContext}.vue`                  | Drag ordering, five-level cap, collapse-all/expand-all                              | The feature                                                      | low             |
| `web-frontend/modules/core/assets/scss/components/views/grid.scss`, `group_bys.scss`, `sortings.scss`     | Grouped-grid styles, logical properties                                             | RTL                                                              | low             |

Deleted: `web-frontend/modules/database/components/view/grid/GridViewGroup(s).vue` and
`utils/groupBy.js` — the code this replaces; `fieldValuesAreEqualInObjects` had no
remaining consumer.

Not ported, deliberately: the 2.3 presence subsystem, the row-context-menu refactor,
the `starts with` view filter and the cookie-namespacing change. All arrive in files
this port merges, none relate to grouping.

**Tests:** `backend/tests/jadawel/contrib/database/{view,api/views}/` — 987 passed,
19 skipped, plus the pre-existing `empty_query` failure noted in
`docs/NEW_FEATURES_PLAN.md`. Frontend: the ported `gridGroupBy` specs (112 tests),
the five new group-by component specs, the 6th-group-by refusal test, and the
store/view/utils/fieldTypes suites (595 passed).

## Upstream 2.3 port — responsive Builder columns and burger menus (2026-09-13)

**Context:** Phase 6 of `docs/NEW_FEATURES_PLAN.md`.

| File                                                                                                                                  | Change                                                                                                  | Reason                                                                                                                                                                                                | Merge risk |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/builder/elements/models.py`                                                                              | `ColumnElement` gains `layout_type`, `column_weights`, `column_stacking`; `MenuElement` gains `variant` | The feature                                                                                                                                                                                           | medium     |
| `backend/src/jadawel/contrib/builder/elements/element_types.py`                                                                       | Serializer fields and validation for both                                                               | The feature                                                                                                                                                                                           | low        |
| `backend/src/jadawel/contrib/builder/migrations/{0069,0070}_*.py`                                                                     | New                                                                                                     | Ported from upstream 0069 and 0072; re-pointed at the fork's builder head because the fork does not port upstream's 0068 or the element-graph migration. Defaults preserve existing desktop rendering | low        |
| `web-frontend/modules/builder/components/elements/components/**`, `page/{PageContent,PagePreview}.vue`, `elementTypes.js`, `enums.js` | Grid layout, layout selector, burger menu, mount-time device dispatch                                   | The feature                                                                                                                                                                                           | low        |
| `web-frontend/modules/core/assets/scss/components/builder/**`                                                                         | Column and menu styles, logical properties                                                              | RTL                                                                                                                                                                                                   | low        |
| `web-frontend/vitest.setup.ts`                                                                                                        | Import `config` from `@vue/test-utils`                                                                  | The Nuxt 4 commit used it without importing it, so every component spec died with a `ReferenceError` before the first test                                                                            | low        |

**Tests:** `backend/tests/jadawel/contrib/builder` — 1016 passed, 155 skipped;
`web-frontend/test/unit/builder` — 172 passed, 1 skipped.

---

## Rich-text floating menu RTL placement (2026-09-09)

| File                                                                         | Change                                                                                                                                                | Reason                                                                                                           | Merge risk |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/core/components/editor/RichTextEditorFloatingMenu.vue` | Derive the floating block menu placement and virtual anchor edge from `<html dir>`, then recreate its Tiptap plugin when the locale direction changes | Keep the block-format tool beside the editor's inline-start edge: physical left in LTR and physical right in RTL | low        |

**Test:** `web-frontend/test/unit/core/components/richTextEditorFloatingMenu.spec.js`.

---

## Row coloring on publicly shared views (2026-09-05)**Context:** Issue #28 story 13 asks for colors on read-only shared views. Core's`PublicViewSerializer` exposes sortings and group_bys but nothing about decorations,so the shared grid/gallery rendered without colors. Exposing decorationconfigurations to anonymous visitors is security-sensitive: a conditional rule'sfilter values can describe hidden data.| File | Change | Reason | Merge risk ||------|--------|--------|------------|| `backend/src/jadawel/contrib/database/views/registries.py` | Added `DecoratorValueProviderType.prepare_value_provider_conf_for_public(view_decoration, public_field_ids)` hook, defaulting to `None` | Opt-in seam: a provider that does not implement it is never exposed publicly; arabase's two providers own their own sanitization | low || `backend/src/jadawel/contrib/database/api/views/serializers.py` | `PublicViewSerializer` gained a `decorations` `SerializerMethodField` that drops unknown types and providers returning `None`, and delegates conf sanitization to the new hook | Anonymous visitors of a shared view now receive the same coloring the members see, minus everything referencing hidden fields | low || `backend/tests/jadawel/contrib/database/api/views/test_view_views.py`, `.../gallery/test_gallery_view_views.py`, `.../grid/test_grid_view_views.py` | Added `"decorations": []` to the exact-response public info assertions | The new serializer key appears in every public view info response | low || `web-frontend/test/unit/database/components/view/viewDecoratorContext.spec.js`, `web-frontend/test/unit/database/table.spec.js`, `web-frontend/test/unit/database/publicView.spec.js` | `beforeEach` calls the fork-owned `scopeOutArabaseRowColoring` helper (`web-frontend/test/helpers/arabaseDecorators.js`) to unregister the fork's two decorator and two value provider types for the duration of each spec | These specs' snapshots enumerate the whole toolbar/decorator registry and the tooltip tests hover the first list item; scoping the fork types out keeps the upstream snapshots valid while the feature stays registered in production. Fork coverage lives in `test/unit/arabase/rowColoring.spec.js` | low |**Tests:**`backend/tests/arabase/test_row_coloring.py` (public sanitization, hidden-fielddropping, default-deny for providers without the hook) and`web-frontend/test/unit/arabase/rowColoring.spec.js` (OR-rule stale-field preflight).## Row coloring field-change query budget (2026-09-05)**Context:** The row-coloring value providers register field lifecycle hooks(`after_field_delete`, `after_fields_type_change`) so stale configurations aredropped when a referenced field is deleted or changes type. Core calls thesehooks once per registered provider, and the original per-field loop addedqueries that scale with field count, breaking two upstream query-budget testson the field change path.| File | Change | Reason | Merge risk ||------|--------|--------|------------|| `backend/tests/jadawel/contrib/database/view/test_view_handler.py` | Raised the budget of `test_field_type_single_field_num_queries` and `test_field_type_changed_two_fields_num_queries` from 9 to 11 (`exact=False`) with comments | The arabase providers add a constant +2 (one batched DELETE for single-select conf, one candidate SELECT for conditional conf); the batched cleanup keeps the cost independent of field count | low |**Test:**`backend/tests/arabase/test_row_coloring.py` (366 passed in `tests/arabase`) and the two bumped tests themselves.

## Reload performance (2026-09-06)

| File                                                                | Change                                                            | Reason                                                                                                             | Merge risk |
| ------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------- |
| `web-frontend/config/nuxt.config.prod.ts`                           | Cache bundled locale messages for 24 hours in production          | Avoid downloading Arabic and English messages again on every reload; the messages URL includes the deployment hash | low        |
| `web-frontend/modules/core/middleware/workspacesAndApplications.js` | Load the workspace/selection branch and applications concurrently | Remove an independent request from the serial startup path while awaiting both branches before navigation          | low        |

**Tests:** `test/unit/config/productionRuntime.spec.js` and
`test/unit/core/middleware/workspacesAndApplications.spec.js` in `web-frontend/`.

## MCP protection CORS header (2026-08-31)

**Context:** CranL's preview hostname serves the Nuxt frontend while its runtime
configuration can point API calls at the canonical Jadawel hostname. MCP policy
create/replace requests carry an `Idempotency-Key`, so cross-origin browsers must
be allowed to include that header in their CORS preflight.

| File                                          | Change                                          | Reason                                                                                                            | Merge risk |
| --------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py` | Added `Idempotency-Key` to `CORS_ALLOW_HEADERS` | Prevent the browser from blocking protected-policy POST/PATCH requests before they reach the additive Arabase API | low        |

**Test:**
`backend/tests/arabase/mcp/protection/test_policy_editing.py::test_policy_replace_cors_preflight_allows_idempotency_header`.

## MCP lifecycle and view-filter query budget (2026-09-01)

**Context:** The protection lifecycle receiver was opening a nested transaction for
every model save, including unprotected objects. Django's delete collector also ran
unneeded discovery queries when removing standalone view sort/group/filter rows during
field-type changes. Both regressions broke existing query-budget tests and obscured
the actual protected-field lifecycle work.

| File                                                    | Change                                                                                          | Reason                                                                                                                                       | Merge risk |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/database/views/handler.py` | Use router-aware `_raw_delete` for standalone incompatible view sort, group-by, and filter rows | Preserve the existing explicit indexing hook while removing collector queries; these models have no dependent cascade receivers in this path | low        |

**Test:** The full backend suite (`pytest tests -q -n 2`) passes with 8,000 passed and
441 skipped; the former 28-test failure set passes in full.

## MCP protection boundary (2026-08-30)

**Context:** Endpoint-specific protected fields need one generic enforcement seam
around every MCP tool call. The fork owns the protection policy and contracts under
`arabase`; core only exposes the interception point and content-blind transport
behavior.

| File                                         | Change                                                                                                                                           | Reason                                                                                                                 | Merge risk |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/core/mcp/registries.py` | Added one optional synchronous call interceptor around `_sync_call`, after input validation and before serialization                             | Let Arabase enforce protection in the same worker-thread and transaction context without editing individual core tools | low        |
| `backend/src/jadawel/core/mcp/errors.py`     | Added an allowlisted safe tool exception and protocol error codes                                                                                | Let the additive protection interceptor fail closed without returning caller-controlled exception text                 | low        |
| `backend/src/jadawel/core/mcp/__init__.py`   | Replaced caller-visible endpoint, tool, and exception strings with fixed `CallToolResult` errors carrying a correlation ID and retryability flag | Prevent arguments, keys, values, and exception text from crossing the MCP error boundary                               | low        |
| `backend/src/jadawel/core/mcp/sse.py`        | Removed request bodies, serialized messages, session URIs/IDs, and validation details from transport logs and failure messages                   | Keep diagnostic sinks content-blind before protected values can traverse MCP                                           | low        |

**Tests:** `backend/tests/jadawel/core/mcp/test_mcp_registries.py`,
`backend/tests/jadawel/core/mcp/test_mcp_server.py`,
`backend/tests/jadawel/core/mcp/test_mcp_sse.py`, and
`backend/tests/arabase/test_mcp_protection_boundary.py`.

### Validation-error hardening (2026-09-02)

The MCP SDK's default JSON Schema validator runs before Jadawel's tool handler and
includes the rejected argument value in its caller-visible error text. Jadawel tools
already validate their Pydantic input schemas inside the handler.

| File                                       | Change                                                                                                   | Reason                                                                                                      | Merge risk |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/core/mcp/__init__.py` | Disabled the SDK's outer input validator while retaining per-tool Pydantic validation inside `call_tool` | Ensure malformed values reach the existing fixed safe-error boundary instead of being echoed to MCP clients | low        |

**Test:**
`backend/tests/jadawel/core/mcp/test_mcp_server.py::test_call_tool_validation_error_does_not_echo_arguments`.

## MCP artifact approval boundary (2026-08-30)

| File                                                      | Change                                                                                     | Reason                                                                                                                            | Merge risk |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/database/api/views/views.py` | Added an optional `before_public_info` hook before the generic public-view serializer      | Let the additive HTML-page view type deny stale or missing protected-artifact approvals before raw page metadata/HTML is returned | low        |
| `backend/src/jadawel/contrib/database/api/views/views.py` | Added an optional `handle_view_update` hook before the generic undoable view update action | Let the additive HTML-page view type route direct REST source edits into a content-blind protected-artifact draft                 | low        |

## Phase 0 — Strip proprietary `premium/` and `enterprise/` (2026-07-03)

**Context:** The Baserow repo is open-core. Per the non-negotiable legal guardrail, the
`premium/` and `enterprise/` directories are proprietary and were **deleted** from the
fork. Baserow already supports an OSS-only mode (`JADAWEL_OSS_ONLY`), so most of core is
designed to run without these plugins; the edits below remove the remaining build/config
references and one runtime dependency on a setting the enterprise plugin used to inject.

| File                                                  | Change                                                                                                                                                                                                                                           | Reason                                                                                                                                 | Merge risk |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py`         | Force `JADAWEL_OSS_ONLY = True` and `JADAWEL_BUILT_IN_PLUGINS = []`; removed `baserow_premium_*`/`baserow_enterprise_*` table names from the CACHALOT lists; added a default for `JADAWEL_ENTERPRISE_USER_SOURCE_COUNTING_TASK_INTERVAL_MINUTES` | Stop loading the deleted plugins; keep cache config referencing only existing tables; provide the setting core still reads (see below) | high       |
| `backend/pyproject.toml`                              | Removed `[tool.uv.workspace] members` (premium/enterprise backends), their pytest `pythonpath` entries; set isort `known-first-party = ["baserow", "arabase"]`                                                                                   | Workspace members no longer exist                                                                                                      | med        |
| `backend/uv.lock`                                     | Regenerated with `uv lock` — dropped `baserow-premium` and `baserow-enterprise`                                                                                                                                                                  | Keep lock consistent with pyproject so `uv sync --frozen` works                                                                        | med        |
| `backend/Dockerfile`                                  | Removed all premium/enterprise `COPY`/`--mount`/`PYTHONPATH`/`mkdir` refs across builder-prod-base, builder-ci, builder-prod, ci, dev, local stages                                                                                              | Those paths/files no longer exist; build would fail                                                                                    | high       |
| `web-frontend/Dockerfile`                             | Removed premium/enterprise `mkdir`/`COPY`/symlink refs across builder-ci, builder-prod, ci, dev stages                                                                                                                                           | Same                                                                                                                                   | high       |
| `web-frontend/config/nuxt.config.base.ts`             | Removed `premiumBase`/`enterpriseBase` params and the block pushing the two plugin `module.js` files                                                                                                                                             | Modules deleted                                                                                                                        | high       |
| `web-frontend/package.json`                           | `test`/`eslint`/`stylelint`/`prettier` scripts no longer reference `../premium`/`../enterprise`; removed `test:premium`/`test:enterprise`                                                                                                        | Paths gone                                                                                                                             | med        |
| `eslint.config.mjs`                                   | Removed premium/enterprise file globs                                                                                                                                                                                                            | Paths gone                                                                                                                             | low        |
| `e2e-tests/package.json`                              | Removed `test-enterprise-only` script                                                                                                                                                                                                            | Enterprise e2e specs gone                                                                                                              | low        |
| `deploy/all-in-one/Dockerfile`                        | Removed premium/enterprise `COPY` + `PYTHONPATH`                                                                                                                                                                                                 | Paths gone                                                                                                                             | med        |
| `deploy/all-in-one/supervisor/default_jadawel_env.sh` | `PYTHONPATH` trimmed to `backend/src`                                                                                                                                                                                                            | Paths gone                                                                                                                             | low        |
| `docker-compose.dev.yml`                              | Removed the premium/enterprise backend & web-frontend bind-mount volume lines (7 services)                                                                                                                                                       | Dirs gone; bind mounts would create empty dirs / error                                                                                 | med        |
| `.github/workflows/ci.yml`                            | Removed premium/enterprise from `paths-filter` and from the `ruff check`/`format` args                                                                                                                                                           | Paths gone (CI is reworked in Task 4)                                                                                                  | med        |
| `config/vscode/.vscode/launch.json`, `settings.json`  | Removed premium/enterprise test paths and mypy/analysis extra paths                                                                                                                                                                              | Dev-editor convenience only                                                                                                            | low        |

### Known remaining upstream references (intentionally left)

- `backend/src/jadawel/core/generative_ai/generative_ai_model_types.py` and
  `.../registries.py` import `baserow_premium.fields.ai_file.AIFile` **only under
  `if TYPE_CHECKING:`**. These are never evaluated at runtime and copy no proprietary
  code (name reference only). Left untouched to minimise core-file churn; will be
  revisited if/when we run `mypy` in CI. **Do not** re-add the `baserow_premium` package.
- `.github/dependabot.yml`, `backend/src/jadawel/test_utils/pytest_conftest.py`,
  `backend/src/jadawel/contrib/database/mcp/services.py`: comment-only mentions. Harmless.

## Phase 0 — Register the `arabase` app / module (2026-07-03)

Additive scaffolding lives in `backend/src/arabase/` and
`web-frontend/modules/arabase/` (not logged individually — they're our files). The
two core files below are edited only to _register_ that additive code:

| File                                          | Change                                                  | Reason               | Merge risk |
| --------------------------------------------- | ------------------------------------------------------- | -------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py` | Appended `"arabase"` to `INSTALLED_APPS`                | Load our Django app  | med        |
| `web-frontend/config/nuxt.config.base.ts`     | Appended `./modules/arabase/module.js` to `baseModules` | Load our Nuxt module | med        |

## Phase 0 — CI (2026-07-03)

Added `.github/workflows/jadawel-ci.yml` (our own, self-contained, secret-free CI:
ruff, Django check + fork-hygiene tests on a Postgres service, eslint, vitest, and
backend+web-frontend Docker image builds). The upstream Baserow workflows are kept
for reference / cheap merges but their auto-triggers are disabled (set to
`workflow_dispatch` only) because they publish to Baserow's own registry/SaaS/project
infra and need their secrets:

| File                                                      | Change                           | Merge risk |
| --------------------------------------------------------- | -------------------------------- | ---------- |
| `.github/workflows/ci.yml`                                | `on:` → `workflow_dispatch` only | med        |
| `.github/workflows/publish-release-images.yml`            | `on:` → `workflow_dispatch` only | low        |
| `.github/workflows/trigger-helm-chart-upload.yml`         | `on:` → `workflow_dispatch` only | low        |
| `.github/workflows/database-projects-issues-workflow.yml` | `on:` → `workflow_dispatch` only | low        |
| `.github/workflows/database-projects-pr-workflow.yml`     | `on:` → `workflow_dispatch` only | low        |

## Phase 0 — Windows-safe i18n locales (2026-07-03)

Upstream ships `web-frontend/i18n/locales` as a **git symlink → `../locales/`** to
satisfy `@nuxtjs/i18n`'s default `restructureDir: 'i18n'` while keeping the real
translation files in `web-frontend/locales/`. On a Windows checkout
(`core.symlinks=false`) that symlink materialises as an 11-byte text file, so the
Nuxt build (and the bind-mounted dev server) fails with
`ENOTDIR … i18n/locales/en.json`.

| File                                      | Change                                | Reason                                                                               | Merge risk |
| ----------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------ | ---------- |
| `web-frontend/i18n/locales` (symlink)     | Removed from git                      | Non-portable; breaks Windows checkouts / bind-mount dev                              | med        |
| `web-frontend/config/nuxt.config.base.ts` | `langDir: 'locales'` → `'../locales'` | Point i18n straight at the real `web-frontend/locales/`, no symlink needed on any OS | med        |

> Note: `.claude/skills` is also a symlink checked out as a file on Windows, but it's
> outside the build/runtime path, so it's left alone.

### Runtime note

`baserow.core.user_sources.handler.update_user_count_...` reads
`settings.JADAWEL_ENTERPRISE_USER_SOURCE_COUNTING_TASK_INTERVAL_MINUTES`, which the
enterprise plugin used to inject. The periodic task that calls it was scheduled by the
enterprise plugin (not core), so this path is effectively dormant in the OSS build, but
we define a safe default (10, a divisor of 60) so it can never raise `AttributeError`.

---

## Phase 1.1 — Arabic locale + RTL direction (2026-07-03)

**Context:** Arabic is Jadawel's **primary** locale (English secondary). This phase
adds `ar` as a first-class language on both tiers and makes the default locale
env-configurable so new installs come up Arabic-first.

| File                                                                      | Change                                                                                                   | Reason                                                                                                                                                                                    | Merge risk |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- | --- |
| `backend/src/jadawel/config/settings/base.py`                             | `LANGUAGE_CODE = os.getenv("JADAWEL_DEFAULT_LOCALE", "ar")`; prepended `("ar", "Arabic")` to `LANGUAGES` | Make Arabic selectable + the env-configurable default; new-user creation reads `settings.LANGUAGE_CODE` live (see `core.user.handler`) so `JADAWEL_DEFAULT_LOCALE` is honoured per deploy | med        |
| `backend/src/jadawel/core/migrations/0115_jadawel_add_arabic_language.py` | **New** AlterField migration for `userprofile.language` (adds `ar` to choices, default `ar`)             | Django requires the migration to live in the model's app (`core`); it's a no-op choices/default change, no data impact                                                                    | low        |
| `web-frontend/config/locales.js`                                          | Added `{ code: 'ar', name: 'العربية', file: 'ar.json', dir: 'rtl' }` (first entry)                       | Activate the `ar` locale across all module langDirs; `dir: 'rtl'` is the source of truth for direction                                                                                    | med        |
| `web-frontend/config/nuxt.config.base.ts`                                 | `defaultLocale` now `process.env.NUXT_DEFAULT_LOCALE                                                     |                                                                                                                                                                                           | 'ar'`      | Arabic-first frontend default, env-overridable to match the backend | med |

**New env var:** `JADAWEL_DEFAULT_LOCALE` (backend, default `ar`) / `NUXT_DEFAULT_LOCALE`
(frontend, default `ar`). Set both to `en` to bring the stack up LTR/English for
comparison during the RTL audit.

**Additive (not core edits, not logged in the table):** `ar.json` translation files in
`web-frontend/locales/` and every module `locales/` dir; the arabase frontend plugin that
sets `<html dir/lang>` reactively from the active locale; `web-frontend/modules/arabase/locales/`;
`docs/GLOSSARY_AR.md`.

---

## Phase 1.2–1.3 — RTL foundation: font, logical properties, icon flip (2026-07-03)

**Context:** Make the app render correctly right-to-left. Approach per the plan:
convert to CSS **logical properties** file-by-file (no blind global regex), ship a
proper Arabic UI font, and add a lint guard. Cross-cutting RTL concerns live in the
additive `modules/arabase/assets/scss/arabase.scss` (not logged here); the rows below
are edits to upstream core files.

| File                                                            | Change                                                                                                                                                               | Reason                                                                                        | Merge risk        |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------- |
| `web-frontend/modules/core/assets/scss/fonts.scss`              | Appended 4 `@font-face` blocks for **IBM Plex Sans Arabic** (weights 400/500/600/700), Arabic `unicode-range`, self-hosted from `static/fonts/ibm-plex-sans-arabic/` | Ship a real Arabic UI face with no runtime CDN (PDPL/KSA self-hosting)                        | low (append-only) |
| `web-frontend/modules/core/assets/scss/variables.scss`          | `$text-font-stack` now `'Inter', 'IBM Plex Sans Arabic', sans-serif`                                                                                                 | Arabic glyphs resolve to Plex per-glyph everywhere; RTL flips priority in arabase.scss        | med               |
| `web-frontend/modules/core/assets/scss/components/layout.scss`  | Converted `.layout__col-1/2/2-1` physical `left/right/inset` to logical (`inset-inline*`)                                                                            | App shell columns must lay out from the inline-start in RTL                                   | med               |
| `web-frontend/modules/core/layouts/app.vue`                     | Inline `:style` `left/right` → `insetInlineStart/insetInlineEnd` on col-2/col-3 and the two resize handles                                                           | Reactive column widths must follow inline direction                                           | med               |
| `web-frontend/modules/core/assets/scss/components/sidebar.scss` | Converted 13 physical props (border-right, padding/margin-left/right, right, radii) to logical equivalents                                                           | Sidebar is inline-start-anchored chrome; must mirror in RTL                                   | med               |
| `web-frontend/stylelint.config.mjs`                             | Added `stylelint-use-logical` plugin: `csstools/use-logical` = `warning` globally, `error` for `modules/arabase/**`                                                  | Turn the ~180-file physical-prop backlog into a visible worklist; hold new fork code strictly | low               |
| `web-frontend/package.json` / `yarn.lock`                       | Added `stylelint-use-logical@^2.1.3` devDependency (lockfile: +5 lines only)                                                                                         | Support the rule above                                                                        | low               |

**Additive (not logged in the table):** `modules/arabase/assets/scss/arabase.scss`
(RTL font priority, Arabic line-height 1.6, directional icon-flip allowlist with a
`.rtl-no-flip` opt-out, `direction: ltr` on numeric/date/identifier grid cells,
`.force-ltr` helpers); the bundled font files + `LICENSE.md` under
`static/fonts/ibm-plex-sans-arabic/`; `modules/arabase/module.js` pushes arabase.scss
into `nuxt.options.css`.

### Deliberately NOT done here (needs the browser + native pass)

The **grid engine RTL** (horizontal virtualisation `scrollLeft` normalisation, frozen
column inline-start stickiness, per-field cell nav) is the deep, high-risk piece. Its
SCSS (`components/views/grid.scss`, ~911 lines) is coupled to JS that sets physical
`left` inline, so a blind conversion would break the grid in **both** directions. It is
left for the mandated visual-regression + native-review pass (`docs/RTL_REVIEW.md` §B);
the arabase layer already fixes cell text direction, which is the data-legibility part.

---

## Phase 0 — Re-freeze `FormView.mode` choices after premium strip (2026-07-03)

`makemigrations --check` failed because `FormView.mode`'s `choices` no longer matched
migration `0086_formview_mode` (which froze `[("form","form"),("survey","survey")]`).

**Root cause (a Phase 0 side-effect, _not_ upstream drift):** the `"survey"` mode was
registered by the **premium** plugin
(`premium/backend/src/baserow_premium/apps.py` → `FormViewModeTypeSurvey`, `type="survey"`),
which we deleted in the premium/enterprise strip (commit `78b504bc6`). `FormView.mode`
uses registry-driven `choices=lazy(form_view_mode_registry.get_choices, list)()`; with
premium gone the OSS registry holds only `"form"`, so the resolved choices dropped to
`[("form","form")]` and diverged from the frozen migration. Pristine upstream 2.2.2 (with
premium installed) passes the check — this divergence is created by our fork.

**Fix:** a new no-op state migration re-freezing the choices to the OSS-only set. The
migration was **hand-written**, not taken verbatim from `manage.py makemigrations`:
under Django 5.2 the autogenerator serializes the `lazy(...)` proxy as the _string_
`"[('form', 'form')]"`, which never compares equal to the live proxy, so the generated
file regenerates itself on every run (`0210`, `0211`, …). Freezing `choices` as a real
Python list `[("form", "form")]` compares equal to the proxy and makes the check stable.

`choices`/`default` are Python-level only, so this touches no schema and no data —
`sqlmigrate database 0209` prints `-- (no-op)`; `makemigrations --check` is clean across
all apps.

| File                                                                          | Change                                                                            | Reason                                                                                                | Merge risk |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/database/migrations/0209_alter_formview_mode.py` | New no-op `AlterField` re-freezing `FormView.mode` choices to `[("form","form")]` | Match the OSS-only form-mode registry after the premium strip; unblock `makemigrations --check` in CI | low        |

> Merge-risk note: only risk is a migration-number collision if a future upstream merge
> also introduces a `0209_*` leaf on `database`; resolve with a standard merge migration.
> Do **not** re-add the `baserow_premium` survey mode to satisfy the old frozen choices.

---

## Phase 1 WP4 — Top bar + panels/dropdowns to logical properties (2026-07-23)

Converted the header (top bar), context menus, dropdowns, select lists, filter/sort/
group-by panels, row-modal chrome, toasts, tooltip content, and the datepicker text
alignment from physical (`left`/`right`) to CSS logical properties so they follow
`dir="rtl"`. Deliberately **left physical**: JS-positioned bits (tooltip
`--tooltip-cursor-position-*` vars, `dropdown__items--fixed` fixed positioning,
`select__items-loading` symmetric centering hack) because their coordinates come from
`getBoundingClientRect` math, which is physical by definition.

Also added the `clientHandler.cannotDisableAllAuthProviders{Title,Description}` i18n
keys (en + ar): the code in `modules/core/plugins/clientHandler.js` references them but
their definitions lived in the **enterprise** locale files we stripped, causing intlify
fallback warnings on every SSR request. Parity gate remains green (3,484/3,484).

| File                                                  | Change                                                                                                                                 | Reason                                                           | Merge risk |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------- |
| `modules/core/assets/scss/components/header.scss`     | full logical-props conversion (incl. loading keyframes, `header__info` float/border, search/buttons/right `margin-inline-start: auto`) | top bar RTL                                                      | low        |
| `modules/core/assets/scss/components/context.scss`    | `text-align: start`, offset/active/deactivated icons + loading spinner to inline props                                                 | context menus RTL (Teleported)                                   | low        |
| `modules/core/assets/scss/components/dropdown.scss`   | selected/toggle icon margins + `--floating`/`--floating-left` anchors to inline props                                                  | dropdown menus RTL                                               | low        |
| `modules/core/assets/scss/components/select.scss`     | item label/link paddings, active icon, indent, footer-create to inline props                                                           | select lists RTL                                                 | low        |
| `modules/core/assets/scss/components/filters.scss`    | 3 props to inline equivalents                                                                                                          | filter panel RTL                                                 | low        |
| `modules/core/assets/scss/components/sortings.scss`   | 5 props to inline equivalents                                                                                                          | sort panel RTL                                                   | low        |
| `modules/core/assets/scss/components/group_bys.scss`  | 5 props to inline equivalents                                                                                                          | group-by panel RTL                                               | low        |
| `modules/core/assets/scss/components/row_modal.scss`  | drag handle + hidden-separator icon margins                                                                                            | row modal RTL                                                    | low        |
| `modules/core/assets/scss/components/toast.scss`      | toast containers anchored `inset-inline-end`                                                                                           | toasts appear inline-end (left in RTL)                           | low        |
| `modules/core/assets/scss/components/tooltip.scss`    | expandable content `text-align: start` only                                                                                            | tooltip text RTL; JS positioning untouched                       | low        |
| `modules/core/assets/scss/components/datepicker.scss` | `text-align: start`                                                                                                                    | datepicker RTL text alignment                                    | low        |
| `web-frontend/locales/en.json` + `locales/ar.json`    | add `cannotDisableAllAuthProviders*` keys                                                                                              | keys orphaned by enterprise strip; kill SSR intlify warning spam | low        |

---

## Phase 1 WP4/WP5 — RTL-aware context positioning (2026-07-23)

Bug (browser-reproduced): in RTL the view filter panel opened anchored by its **left**
edge (callers pass `horizontal: 'left'`, an LTR assumption), so when its content grew
(empty state 346px → one filter row 681px) it overflowed ~227px past the right edge of
the viewport. The stock `checkForEdges` flip only helps when the panel is already wide
at open time, not when it grows after opening.

Fix in `Context.vue#calculatePositions`: when `document.documentElement.dir === 'rtl'`,
mirror the caller's `horizontal` anchor (`left`↔`right`) **and negate
`horizontalOffset`** (a positive offset means "push towards physical +x" in the stock
code; mirrored it must push towards −x). Without the negation, contexts anchored to
edge-flush triggers (e.g. the sidebar workspace selector, offset 16) compute
`css.right = -16`, trip the "doesn't fit" guard at the top of `updatePosition`, and
silently never open. `checkForEdges` still flips on real overflow after the mirror.
One central change mirrors every context/panel/dropdown in the app.

| File                                               | Change                                                                               | Reason                                                                                                                         | Merge risk                                                                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `web-frontend/modules/core/components/Context.vue` | Mirror `horizontal` + negate `horizontalOffset` in `calculatePositions` when dir=rtl | RTL panels must anchor inline-start and grow towards content; fixes off-screen filter panel + never-opening workspace selector | medium — upstream touches this method occasionally; re-apply block is 12 lines at the top of `calculatePositions` |

---

## Phase 1 WP4 — over-constrained absolute boxes in RTL (2026-07-27)

One CSS bug class produced three separate RTL-only failures. A box with a
definite width plus **both** `left` and `right` is over-constrained, so CSS drops
one of them — `right` under LTR, but **`left` under RTL**. Every instance was
invisible in English and broken in Arabic.

`.dropdown__items` sets both inline insets to `0` (the base rule lets a nested
menu stretch to its trigger). The `--fixed` variant is `position: fixed` and
receives a physical inline `left` from JS with no matching `right`, so cancelling
only `inset-inline-end` left a stray `right: 0` alive under RTL and stretched the
"add field" menu across the whole viewport (measured 1892px wide). Releasing both
inline sides fixes it (measured 351px, fully on screen).

| File                                                | Change                                                                     | Reason                                                                                                | Merge risk                                                |
| --------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `modules/core/assets/scss/components/dropdown.scss` | `.dropdown__items--fixed`: `inset-inline-end: auto` → `inset-inline: auto` | Release _both_ inline insets; a JS-supplied physical `left` must not combine with the base `right: 0` | low — 1 line, adjacent to the existing `--floating` patch |

---

## Templates — tolerate types this build does not ship (2026-07-27)

Bug (reproduced): the template picker was empty. `/api/templates/` returned `[]`
and `core_template` had 0 rows, because **every bundled template failed to
install**. Stripping `premium/` and `enterprise/` leaves several registries
empty, and the import path treated a missing type as fatal:

- `view_type_registry` has only grid/gallery/form — `timeline`, `kanban` and
  `calendar` are proprietary, and 118 of the 155 templates use at least one.
- `field_rules` is missing `date_dependency`.
- `user_source_type_registry` is empty (`local_baserow` lived in enterprise),
  which aborted the whole `sync_templates` run rather than one template.

Verified before changing anything: of the 816 tables across all templates,
**none** would be left without a view, since every table has a grid/gallery/form
view. Skipping a proprietary view therefore degrades cleanly — the table and its
data import, only that one view is absent.

No proprietary code was copied or reimplemented to fix this.

| File                                                        | Change                                                                                                                     | Reason                                                                                                                                                                                                               | Merge risk                                     |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `backend/src/jadawel/contrib/database/application_types.py` | `_import_table_views`: catch `ViewTypeDoesNotExist`, log and skip the view instead of aborting the application import      | An export made where kanban/calendar/timeline exist must still import here                                                                                                                                           | medium — small block inside an upstream loop   |
| `backend/src/jadawel/contrib/database/application_types.py` | `_import_field_rules`: catch `InstanceTypeDoesNotExist`, log and skip the rule (reads `type` before `import_rule` pops it) | Same, for the proprietary `date_dependency` rule                                                                                                                                                                     | low                                            |
| `backend/src/jadawel/core/handler.py`                       | `sync_templates`: wrap the per-template `_sync_template` call in try/except, collect failures, log a summary at the end    | One unimportable template must not abort the sync of the other 154; each template already has its own atomic block so the rollback is clean                                                                          | medium — upstream occasionally edits this loop |
| `backend/src/jadawel/contrib/builder/application_types.py`  | `import_user_sources_serialized`: catch `InstanceTypeDoesNotExist`, log and skip the user source                           | `user_source_type_registry` is empty (`local_baserow` was enterprise); without this the builder app and its databases are lost                                                                                       | low                                            |
| `backend/src/jadawel/contrib/builder/pages/handler.py`      | `import_elements`: drop elements whose type is unregistered, plus their descendants, before the priority sort              | The sort key itself resolves every type through the registry, so an unknown type raised _before_ the import loop. Descendants are removed to a fixed point because parents are not guaranteed to be serialized first | medium                                         |
| `backend/src/jadawel/contrib/builder/pages/handler.py`      | `import_workflow_actions`: skip actions whose `element_id` is absent from `id_mapping`                                     | An action bound to a skipped element raised `KeyError` and aborted the page                                                                                                                                          | low                                            |

Chain of missing types encountered, in the order they surfaced: `view_type`
(timeline/kanban/calendar) → `field_rules` (date_dependency) → `user_source`
(local_baserow) → `element_type` (auth_form, input_file) → workflow actions
orphaned by the skipped element. Templates went 0 → 24 → 123 → 155 as each was
handled.

---

## Jadawel theme — sage/emerald palette (2026-07-28)

Retones the interface from Baserow's blue to a calm sage/emerald, and adds a
faint grid behind the working area.

The important structural change is in `colors.scss`. The `$colors` map is
**user data** — its keys are what get written to the database when someone
picks a colour for a select option or a view — but it was reading the semantic
`$color-*` tokens. Repointing `$color-primary-*` at the brand would therefore
have silently repainted colours people already chose, and a select option
labelled "blue" would have come back green. The map now reads raw `$palette-*`
values only, with the greys frozen to their pre-sage hex. Verified: all 42
entries resolve byte-identically before and after.

34 component stylesheets referenced `$palette-blue-*` directly for chrome
(buttons, inputs, checkboxes, tabs, toasts, focus rings) rather than going
through `$color-primary-*`, so repointing the semantic token alone left the
primary button blue. All 78 occurrences were moved to `$palette-brand-*`.

`$palette-brand-500` is pinned at `#278053` rather than a lighter, more
saturated green: -500 is the step that carries white text, and the lighter
value measured 3.93:1 against white, failing WCAG AA. `#278053` measures
4.89:1. Verified in-browser after the change.

| File                                                                            | Change                                                                                                                       | Reason                                                                         | Merge risk                        |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | --------------------------------- |
| `web-frontend/modules/core/assets/scss/colors.scss`                             | Add `$palette-brand-*`; tint neutrals sage; repoint `$color-primary-*` at brand; decouple `$colors` map from semantic tokens | Brand retone without touching stored user colours                              | medium — upstream edits this file |
| `web-frontend/modules/core/assets/scss/base.scss`                               | Faint brand-derived grid on `body`, 32px, fixed attachment                                                                   | Texture behind the transparent `.layout__col-2-scroll`                         | low                               |
| 34 × `web-frontend/modules/core/assets/scss/**`                                 | `$palette-blue-*` → `$palette-brand-*` (78 occurrences)                                                                      | Chrome bypassed the semantic token                                             | medium — mechanical, re-runnable  |
| `backend/templates/{all-fields,custom-code-demos,formulas,password-reset}.json` | Category `"Baserow"` → `"Examples"`                                                                                          | A template category named after the upstream project was visible in the picker | low                               |

---

## Arabic and English only (2026-07-28)

Drops every language except Arabic and English across both tiers: 113 frontend
locale JSON files, 53 backend `locale/<lang>` directories with their .po/.mo
catalogues, and the eight surplus entries in each of the two language lists.

Three things this touched that are easy to miss:

- `UserProfile.language` takes `choices` from `settings.LANGUAGES`, so trimming
  the list is a model change and needs a migration, not just a settings edit.
- Dropping a language does not touch rows that already hold it. A user sitting
  on `fr` would keep requesting a locale the frontend can no longer resolve, so
  the migration also normalises those rows to the default. It is deliberately
  one-way — the original values are overwritten, and reversing restores the
  choices but not the users' previous languages.
- `modules/builder/plugin.js` imported seven locale JSON files that nothing in
  the file used. Dead as they were, they still broke the build the moment the
  files were deleted. Two further modules referenced deleted locales from inside
  commented-out legacy blocks; those were inert but cleaned for consistency.

Backend Arabic was already absent upstream (there is no `locale/ar` catalogue),
so server-side strings such as e-mails fall back to the English msgid. That is
pre-existing, not a regression from this change.

Verified: `makemigrations --check` reports no drift; `PATCH /api/user/account/`
rejects `fr` with "Only the following language keys are valid: ar,en" and
accepts both `ar` and `en`; the login language switcher offers exactly العربية
and English; locale parity stays 3469/3469 with strict mode clean.

| File                                                                      | Change                                        | Reason                                                           | Merge risk |
| ------------------------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- | ---------- |
| `web-frontend/config/locales.js`                                          | Keep `ar` + `en`                              | Single source of truth for the frontend language list            | low        |
| `backend/src/jadawel/config/settings/base.py`                             | `LANGUAGES` → `ar`, `en`                      | Drives `UserProfile.language` choices and API validation         | low        |
| `backend/src/jadawel/core/migrations/0116_jadawel_arabic_english_only.py` | New: alter choices + normalise stranded users | Model change; orphaned rows would request an unresolvable locale | low        |
| `web-frontend/modules/builder/plugin.js`                                  | Remove 7 unused locale imports                | Dead imports that broke the build once the files were gone       | low        |
| 113 × `web-frontend/**/locales/*.json`, 53 × `backend/**/locale/<lang>/`  | Deleted                                       | Unshipped languages                                              | low        |

---

## Sidebar simplification (2026-07-28)

The panel was hard to read for three reasons that compound: you could not tell
which row was selected, table rows carried no glyph, and four one-item sections
each paid for a heading, a `+` and a separator.

**Selection was invisible.** `.tree__item.active`, `.tree__action:hover` and
`.tree__sub:hover` all resolved to the same `rgba($palette-neutral-1300, 0.04)`,
so the open table and the row under the cursor were the same colour. Selection
now carries the brand tint, brand text, a brand icon and a 3px marker bar;
hover keeps the neutral wash. Where a row is both, `.active` wins on source
order. These two states must never resolve to the same value again.

**Tables had no icon.** A database with a dozen tables was a dozen identical
lines of text. Every row now shows `iconoir-table` — the same glyph the search
results already use for a table — except synced tables, which keep the sync
icon rather than showing two.

**`tree.scss` was written in physical directions** while the rest of the
codebase uses logical ones: the sub-item indent, the connector line, the row
menu, the counter and the loading spinners were all pinned to the LTR side and
did not mirror in Arabic. Converted; verified that toggling `dir` produces an
exact mirror, so LTR geometry is byte-for-byte what upstream shipped.

**Workspace utilities became an icon row.** Notifications, members, invite and
trash were five labelled rows costing ~170px above the fold; they are now 30px
icon buttons under the workspace picker. The whole block is 92px. The sidebar's
own search box went with them — global search stays reachable as the first icon,
and the Ctrl/⌘ K hint the box used to show moved into its tooltip. Every icon
carries a tooltip and an `aria-label`; the member count moved into the members
tooltip rather than being dropped.

**The four application sections became one list.** Applications now sort on
`order` alone, which is correct because `Application.order` is allocated per
workspace — the grouped rendering was re-sorting one workspace-wide sequence
inside each type. A side effect is that a database and a dashboard can now be
dragged past each other, which the backend already accepted. The per-type `+`
buttons are gone; the "add new" menu at the foot of the panel already offers
every creatable type plus templates and import.

Not done, deliberately: the collapse control stays in `SidebarFoot`. Moving it
into the utility row would have removed the expand affordance when the sidebar
is collapsed, because that row is inside the block hidden by `v-show`.

Verified in the running app in Arabic: five utility buttons with correct labels,
no search box, zero headings, zero separators, active `rgb(240,247,243)` against
hover `rgba(8,11,7,0.04)`, marker and row menu on the correct inline edges in
both directions, stylelint clean on both stylesheets, locale parity 3470/3470.

| File                                                                    | Change                                                                                          | Reason                                                      | Merge risk                        |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------- |
| `web-frontend/modules/core/assets/scss/components/tree.scss`            | Distinct active state + `%tree-active-marker`; `.tree__sub-icon`; physical → logical properties | Active was indistinguishable from hover; RTL did not mirror | medium — upstream edits this file |
| `web-frontend/modules/core/assets/scss/components/sidebar.scss`         | Replace `.sidebar__search*` with `.sidebar__utilities` / `.sidebar__utility` / badge override   | Search box removed, utilities became icons                  | medium                            |
| `web-frontend/modules/core/components/sidebar/SidebarMenu.vue`          | Utilities as icon buttons; tooltips + aria-labels; Ctrl/⌘ K in the search tooltip               | ~140px reclaimed above the fold                             | medium                            |
| `web-frontend/modules/core/components/sidebar/SidebarSearch.vue`        | Deleted                                                                                         | Its only caller was `SidebarMenu`                           | low                               |
| `web-frontend/modules/core/components/sidebar/SidebarWithWorkspace.vue` | One flat application list; drop headings, per-type `+`, separators                              | Chrome outweighed content                                   | medium                            |
| `web-frontend/modules/database/components/sidebar/SidebarItem.vue`      | Table glyph on every row                                                                        | Rows were undifferentiated text                             | low                               |
| `web-frontend/modules/core/locales/{en,ar}.json`                        | Add `sidebar.searchTooltip`                                                                     | Keeps the keyboard shortcut discoverable without the box    | low                               |

---

## Workspace utilities move to the content header (2026-07-28)

Follow-up to the sidebar work above. The utility icons were still inside the
sidebar, which put them top-right in Arabic; they belong in the top-left corner
of the content area, next to where the eye already goes for search. And with a
magnifier in both places the app showed two search icons that did different
things.

`AppUtilities.vue` now renders notifications, members, invite and trash, pinned
to the top inline-end corner of `.layout__col-2`. It is mounted once by the app
layout rather than by each header, because there are five separate header
components — table, dashboard, automation, builder, workspace home — and the
group has to appear on all of them. The band it occupies is reserved by the
headers themselves via `padding-inline-end: $app-utilities-band`; each is a flex
row whose end-side content is pushed over with `margin-inline-start: auto`, so a
padding on the container is sufficient and no header needs to know the group
exists. The workspace home page has a 74px header rather than the shared 51px
one, so a `:has()` rule matches the group's height to it.

There is deliberately no search icon in the group. The two searches were never
the same feature: the sidebar box was the global Ctrl/⌘ K search, while the
magnifier in the view header is `ViewSearch`, which searches rows in the table
you are looking at. `ViewSearch` has no keyboard shortcut — the magnifier is its
only affordance — whereas global search keeps Ctrl/⌘ K, so dropping the global
icon is the one that loses nothing outright.

The cost, stated plainly: global search now has no visible affordance anywhere.
On a table page there is exactly one magnifier and it searches that table; on
the workspace home and dashboards there is none. If that proves wrong, the fix
is to put the global-search icon back into the group and remove `ViewSearch`
from the view header instead.

Verified in the running app: on a table page the group sits at 0–142px with the
view search starting at 152px and exactly one magnifier on the page; on the
workspace home the group matches the 74px header and centres on it, with the
header's own controls starting flush at 142px. Toggling `dir` moves the group
from the far left to the far right, which is the conventional corner in English.

| File                                                                     | Change                                                             | Reason                                    | Merge risk |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------ | ----------------------------------------- | ---------- |
| `web-frontend/modules/core/components/AppUtilities.vue`                  | New: the four utility buttons                                      | Must appear on every page, not per header | low        |
| `web-frontend/modules/core/assets/scss/components/app_utilities.scss`    | New: pinned band, button and badge styles                          | —                                         | low        |
| `web-frontend/modules/core/layouts/app.vue`                              | Mount `AppUtilities` in `layout__col-2`; drop the dead search emit | Single mount point for every page         | medium     |
| `web-frontend/modules/core/assets/scss/components/layout.scss`           | `.layout__col-2-1` reserves the band                               | Five headers share this class             | medium     |
| `web-frontend/modules/core/assets/scss/components/dashboard.scss`        | `.dashboard__header` reserves the band                             | Workspace home has its own taller header  | low        |
| `web-frontend/modules/core/assets/scss/variables.scss`                   | Add `$app-utilities-band`                                          | Consumed by both header stylesheets       | low        |
| `web-frontend/modules/core/components/sidebar/{SidebarMenu,Sidebar}.vue` | Remove the icon row and the search emit chain                      | Moved to the content header               | medium     |
| `web-frontend/modules/core/locales/{en,ar}.json`                         | Remove `sidebar.searchTooltip`                                     | Its only consumer is gone                 | low        |

## Phase — Arabic terminology pass + hide unfinished app types (2026-07-29)

**Context:** A product-language pass over the Arabic UI, plus temporarily removing two
application types from the creation flow. Six of the seven changes are pure locale-value
edits (no keys added or removed — parity stays 3469/3469). The seventh, the default view
name, could not be fixed in the frontend at all: `TableHandler.create_table` names the
view with `_("Grid")` inside `translation.override(user.profile.language)`, so the name is
**stored as literal text** at creation time and rendered as data thereafter.

Upstream ships no `ar` backend catalogue (noted in the Phase 0 language strip above), so
that gettext call had nothing to translate to and every Arabic user's tables were created
with a view literally named "Grid". This adds the catalogue — the first Arabic backend
translations in the fork — and a data migration to rewrite the rows created before it
existed. Adding the catalogue alone would have fixed only newly created tables.

The `.mo` is committed alongside the `.po` because nothing in the build runs
`compilemessages` — the same convention upstream already follows for `en`.

**Application types:** `builder` ("تطبيق") and `automation` ("أتمتة") are hidden from the
"add new" context via the existing `canBeCreated()` hook rather than by deleting the
registrations. Existing applications of both kinds keep loading, routing and rendering
normally; only the creation entry point is gone. Both surfaces that offer creation
(workspace home and the sidebar) share `CreateApplicationContext`, so one hook covers both.
Reverting is a one-line change per file.

**Terminology:** "لوحة التحكم" → "لوحة البيانات" is applied to the `applicationType.*` keys
only — the dashboard _application type_. `sidebar.dashboard`, `dashboard.title` and
`adminType.dashboard` still read "لوحة التحكم" because they name the workspace home and the
admin area, which are different things that happened to share a translation.

| File                                                                                        | Change                                                                                                                           | Reason                                                                                                               | Merge risk |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/builder/applicationTypes.js`                                          | Add `canBeCreated() { return false }`                                                                                            | Hide "تطبيق" from the add-new context without unregistering the type                                                 | low        |
| `web-frontend/modules/automation/applicationTypes.js`                                       | Add `canBeCreated() { return false }`                                                                                            | Same, for "أتمتة"                                                                                                    | low        |
| `web-frontend/locales/ar.json`                                                              | `applicationType.dashboard{,s,DefaultName}` → "لوحة البيانات"; `common.summarize` → "تحليل"; `viewType.grid` → "جدول"            | Product terminology; `common.summarize` is the grid footer aggregation row                                           | low        |
| `web-frontend/modules/core/locales/ar.json`                                                 | `createApplicationContext.fromTemplate` → "القوالب الجاهزة"                                                                      | Reads as a destination, not a preposition                                                                            | low        |
| `web-frontend/modules/database/locales/ar.json`                                             | `databaseDashboardResourceLinks.title` → "API"; `viewGroupBy.groupBy` + `viewGroupByContext.{groupBy,noGroupByTitle}` → "مجموعة" | "API" is the term users actually search for; "تجميع" collided with the rollup field type                             | low        |
| `backend/src/jadawel/contrib/database/locale/ar/LC_MESSAGES/django.{po,mo}`                 | New: first Arabic backend catalogue; translates `"Grid"` → "جدول"                                                                | The view name is picked in the backend under `translation.override`; untranslated entries still fall back to English | low        |
| `backend/src/jadawel/contrib/database/migrations/0210_jadawel_rename_default_grid_views.py` | New: rename views named exactly `"Grid"` → `"جدول"`, reversible                                                                  | The catalogue fixes new tables only; existing rows hold the untranslated literal                                     | low        |

### Known limitation

`fieldType.rollup` is still "تجميع". It is a different concept (the rollup field type) that
upstream happens to translate with the same Arabic word as group-by; renaming it was out of
scope for this pass and needs its own term.

## Phase — Workspace home: data-bearing database list (2026-07-29)

**Context:** The workspace home page led with two static blocks — "suggested templates"
(two cards hardcoded in `workspace.vue`) and "resources" (one plugin-provided API link) —
and only then showed the user's own applications, each labelled with nothing but its type
and creation date. This moves the application list to the top, adds real counters to it,
and puts per-database actions on the card.

**The reorder needed a stylesheet change, not just a template change.** `.dashboard__main`
is a flex column and `.dashboard__extras` carried `order: 1` / `order: 0` (wide screens),
so DOM order was being silently overridden — upstream used `order` to place the block
above the list on desktop while keeping it below on mobile. Reordering the template alone
would have had no effect above 1280px. Both `order` declarations are removed so the markup
is the single source of truth.

**Counters are a separate endpoint, not extra fields on the application payload.** That
payload is fetched on every route because the sidebar depends on it; row counting is the
expensive part, and folding it in would make every page load pay for a number only the home
page renders. `GET /api/arabase/workspace/<id>/database-stats/` is fetched client-side after
first paint, and failures are swallowed — the cards are fully usable without the numbers.

**Row counts are counted live.** `TableUsage.row_count` exists but is written by the
periodic `run_calculate_storage` task, which is gated behind the instance setting
`track_workspace_usage` — off by default, so the table was empty for all 845 tables on the
dev instance, and even when enabled it lags by up to 30 minutes. Each Baserow table is a
real Postgres table, so exact counts mean one `COUNT(*)` each. Through the ORM that costs a
dynamic model build per table (measured: ~370ms for 14 tables); as a single `UNION ALL` of
plain counts it is ~4ms for the same 14. The endpoint does the latter, caps the fan-out at
200 tables, and returns `rows_exact: false` with a null count past that rather than a
partial total.

**Export is the only genuinely new action.** Rename, duplicate, snapshots, trash and delete
were already in the `⋮` menu of the dashboard card — that menu has always rendered
`getApplicationContextComponent(application)`, the same component the sidebar uses.
`ExportWorkspaceModal` gained an optional `application` prop; when set it preselects that
one application, replaces the application picker with an empty slot so the scope cannot be
widened, and retitles. Passing nothing keeps the workspace-wide behaviour the workspace
context menu relies on.

The `$tc` helper does not exist in this build of vue-i18n. Pluralised keys are called as
`$t(key, { count })`, which is what the rest of the app already does.

| File                                                                           | Change                                                                                                                                    | Reason                                                                    | Merge risk |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/core/pages/workspace.vue`                                | Move `.dashboard__extras` after `.dashboard__wrapper`; fetch and pass `databaseStats`                                                     | Put the user's data first; feed the cards                                 | med        |
| `web-frontend/modules/core/assets/scss/components/dashboard.scss`              | Drop both `order` declarations on `.dashboard__extras`                                                                                    | They overrode DOM order and made the template reorder a no-op on desktop  | low        |
| `web-frontend/modules/core/components/dashboard/DashboardApplication.vue`      | New `stats` prop; render table/column/row counts                                                                                          | The counters                                                              | low        |
| `web-frontend/modules/arabase/services/databaseStats.js`                       | New: client for the stats endpoint                                                                                                        | —                                                                         | low        |
| `web-frontend/modules/core/components/export/ExportWorkspaceModal.vue`         | Optional `application` prop: scoped title, preselection, picker suppressed                                                                | Export one database from its own menu                                     | med        |
| `web-frontend/modules/core/components/export/ExportWorkspaceForm.vue`          | Optional `initialApplicationIds` prop                                                                                                     | Null keeps the select-all default                                         | low        |
| `web-frontend/modules/database/components/application/ApplicationContext.vue`  | Add the export item + modal inside `#additional-context-items`                                                                            | Core renders no default slot, so anything outside a named slot is dropped | low        |
| `web-frontend/modules/core/locales/{en,ar}.json`                               | `dashboardApplication.{table,field,row}Count`, `sidebarApplication.exportDatabase`, `exportWorkspaceModal.application{Title,Description}` | —                                                                         | low        |
| `backend/src/arabase/api/{database_stats,views,urls}.py`, `arabase/plugins.py` | New: the stats endpoint, mounted under `/api/arabase/` via `plugin_registry`                                                              | Additive; no core url file touched                                        | low        |
| `backend/src/arabase/apps.py`                                                  | Register `ArabasePlugin` in `ready()`                                                                                                     | First use of the registry hook the file was written for                   | low        |

### Known limitations

- Arabic plural forms use the repo's existing three-form convention, so counts above ten
  read "94 أعمدة" where strict grammar wants "94 عمودًا". The grid footer already says
  "200 صفوف"; fixing it properly means adding Arabic CLDR plural rules to `i18n.config.ts`
  and is a separate change.
- Counters cover databases only. Other application types render as before.

---

## Workspace home: overview charts, template cards, resources (2026-07-29)

The section under the application list was three problems at once. The two
"suggested templates" were a hardcoded array of English slugs in `workspace.vue`,
so an Arabic-first product advertised English templates and never surfaced the
Arabic ones this fork ships. The "view more" tile rendered as an empty white box
that reads as a failed image load. And both panels were stretched to
`calc(100% - 33px)` so each matched its neighbour's height rather than its own
contents — the resources block was 190px of white around a single link.

**Overview strip.** Four stat tiles plus two charts, above the templates, because
it is the only part of that area that reflects the user's own data. Rows, tables
and members are separate tiles rather than one chart: they are 279, 14 and 1, and
forcing measures of different magnitude onto shared axes — or worse two y-axes —
is the standard way a chart misleads.

`DashboardBarChart` plots rows per database, single hue, no legend (one series;
the row labels carry identity), bars scaled against the largest value rather than
the total so a small database is still visible. `DashboardAreaChart` plots rows
added per day with a crosshair, tooltip, keyboard arrow-key traversal, and a
visually-hidden table — the bar chart needs no table because every value is
already text beside its bar. Both are hand-rolled SVG/CSS: no chart library, so
no runtime CDN fetch.

**The time axis deliberately does not mirror.** It reads left-to-right in Arabic
too. Mirroring a time series is a known source of misreading and Arabic-language
dashboards overwhelmingly keep time flowing this way.

**Backend.** `/arabase/workspace/{id}/activity/` aggregates `created_on` across
every user table, capped and reported the same way the counters are. The
alternatives were all worse: `TableUsage` has no history and is off by default,
`RowHistory` records only edits and is pruned, and the audit log is an enterprise
feature this fork must not read.

Two bugs found while verifying, both of which looked fine on screen:

- `$i18n.locale` is a **ref** inside `<script setup>` and a **string** through the
  options API. Indexing the slug map with the ref missed silently and fell back
  to English, while `$i18n.t` still returned Arabic — so the cards rendered
  Arabic names that opened the English templates. Fixed with `unref`.
- Arabic number agreement. vue-i18n applies the English plural rule to every
  locale, so 200 rows read `200 صفوف` and 24 columns `24 أعمدة`; Arabic takes the
  singular above ten. Supplying a custom rule does not work — this build of
  @nuxtjs/i18n honours neither `pluralizationRules` nor `pluralRules` from
  `i18n.config.ts`, and both were tried; the runtime kept returning the dual form
  for every count above one. The category is now resolved with `Intl.PluralRules`
  (CLDR is in the browser) and used to pick a plain message key. Counts render
  `200 صف`, `24 عمودًا`, `13 صفًا`, `6 أعمدة`.

Only `dashboardApplication`'s three count messages were converted. The other 24
Arabic plural messages still use vue-i18n's pipe syntax and the English rule;
converting one is a local edit to that message plus a `counted()` call, with no
further code change.

Verified in the running app in both languages: tiles 3/14/279/1, bars at 100/33/6.5
percent with the rounded end on the data side in both directions, hover tooltip
and crosshair, activity path drawn from the live endpoint, Arabic cards opening
`arabic-project-management`, English cards opening `project-management`, resources
row 38px instead of 190px. Backend 8/8 pytest, frontend 9/9 vitest, stylelint
clean, locale parity 3501/3501.

| File                                                                                                     | Change                                                               | Reason                                               | Merge risk |
| -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------- | ---------- |
| `backend/src/arabase/api/activity.py`                                                                    | New: rows-created-per-day aggregation                                | No non-enterprise source for row history             | low        |
| `backend/src/arabase/api/{views,urls}.py`                                                                | New `WorkspaceActivityView`                                          | —                                                    | low        |
| `backend/tests/arabase/test_workspace_activity.py`                                                       | New: 8 tests                                                         | Density, trashed rows, window, clamping, permissions | low        |
| `web-frontend/modules/arabase/services/workspaceActivity.js`                                             | New service                                                          | —                                                    | low        |
| `web-frontend/modules/core/components/dashboard/Dashboard{Overview,BarChart,AreaChart,TemplateCard}.vue` | New                                                                  | Overview strip and redesigned cards                  | low        |
| `web-frontend/modules/core/pages/workspace.vue`                                                          | Locale-aware featured templates; mount overview; fetch activity      | Hardcoded English slugs; `unref` bug                 | medium     |
| `web-frontend/modules/core/assets/scss/components/dashboard.scss`                                        | Chart, tile and card styles; unstretch both panels                   | Panels were sized to each other, not their contents  | medium     |
| `web-frontend/modules/core/utils/plural.js`                                                              | New: CLDR category via `Intl.PluralRules`                            | vue-i18n's rule is English-only                      | low        |
| `web-frontend/modules/core/components/dashboard/DashboardApplication.vue`                                | Resolve counts through `pluralKeys`                                  | Arabic number agreement                              | low        |
| `web-frontend/scripts/check-locale-parity.mjs`                                                           | Allow `two`/`few`/`many` without an English twin                     | Categories Arabic needs and English lacks            | low        |
| `web-frontend/modules/core/locales/{en,ar}.json`                                                         | Overview/chart/template strings; count messages as per-category keys | —                                                    | low        |

## Grid keyboard navigation follows field order in RTL (2026-07-29)

Arrow keys name a physical direction; grid navigation moves along the field
order, which is an inline axis. `ArrowLeft` was mapped straight onto "previous
field", which is only true in LTR — in an Arabic grid the previous field sits to
the _right_ of the selected cell, so every horizontal arrow moved the selection
away from the key the user pressed. Reported as: pressing left goes right and
right goes left.

The swap happens once, where the key becomes a direction, so both `Tab` and the
vertical arrows are untouched: `Tab` already means "next in reading order",
which _is_ the field order, and rows stack top to bottom in both directions.

The direction is read from `.grid-view`, not from the cell. Number, date, url,
email and phone cells are pinned to `direction: ltr` in `arabase.scss` so their
digits stay readable; reading the cell would have left the arrows inverted in
exactly those columns and correct everywhere else.

Shift+arrow multi-select had the same inversion, plus a second bug behind it:
its scroll-into-view rectangle is accumulated in field order — an inline
position — but `scrollToElementRect` measures from the container's left edge.
The two coincide only in LTR. It now normalises `scrollLeft` (browsers report it
negative in RTL) and mirrors the finished rectangle across the viewport.

Verified in the running app in Arabic: selection steps 523 → 323 → 91 px on
`ArrowLeft`, back the same way on `ArrowRight`, crosses into the frozen primary
column at the far right, `Tab` still moves toward inline-end, `ArrowDown` holds
its column. Shift+arrow extends field 1 → 5 and scrolls to `scrollLeft: -671`,
landing the last field 20px inside the viewport. The same sequence with `dir`
toggled to `ltr` produces the exact mirror (`+671`), so LTR is unchanged.
7/7 new vitest; the 4 pre-existing snapshot failures in
`test/unit/database/components/view/grid` were confirmed identical with the
change stashed.

| File                                                              | Change                                                   | Reason                                                              | Merge risk |
| ----------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/database/utils/gridViewKeyboard.js`         | New: `toInlineArrowKey`, `mirrorInlineRect`              | Pure helpers, testable without a grid                               | low        |
| `web-frontend/test/unit/database/utils/gridViewKeyboard.spec.js`  | New: 7 tests                                             | Swap, vertical/Tab pass-through, rect mirroring                     | low        |
| `web-frontend/modules/database/mixins/gridField.js`               | Swap horizontal arrows before mapping to a direction     | Arrows were inverted in RTL                                         | low        |
| `web-frontend/modules/database/components/view/grid/GridView.vue` | Same swap for shift+arrow; inline-normalised scroll rect | Multi-select inverted; scroll rect was inline, consumed as physical | medium     |

## Workspace home: two applications per row (2026-07-29)

The application list was a single flex column, so on a wide screen each row was
a ~1900px band holding a 40px icon, a short name and one line of counters. The
list is now a two-column grid.

`minmax(0, 1fr)` rather than `1fr` for the tracks: `1fr` is `minmax(auto, 1fr)`,
and `auto` refuses to shrink below the widest counter line, which would push the
columns out of the container instead of letting the existing text ellipsis do
its job.

Grid rows are as tall as their tallest cell, so each `li` is a flex column and
the application block takes up the slack. Without that the two hairline
separators in a row sit at different heights as soon as one application's name
wraps and its neighbour's does not.

Below `$dashboard-applications-breakpoint` it falls back to one column. The
number is measured, not guessed: the longest counter line in the seeded
workspace ("قاعدة بيانات • 10 جداول • 94 عمودًا • 66 صفًا • تاريخ الإنشاء منذ
ساعات") needs 362px of text plus 76px of icon, gap and padding, so two columns
and the 32px gap want ~910px of list, and the sidebar plus the utility band take
a further ~318px off the viewport. At 1200px the counters were clipping and the
creation date was the first thing lost; 1280px clears it.

Nothing was needed for RTL — grid flow follows the writing direction on its own.
Verified at 1400px: first application in the right column in Arabic, in the left
column with `dir` toggled to `ltr`, separators aligned per row, no clipped
counter lines; at 1279px a single 961px column.

| File                                                              | Change                                                                                               | Reason                                            | Merge risk |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ---------- |
| `web-frontend/modules/core/assets/scss/components/dashboard.scss` | `.dashboard__applications` flex column → two-column grid; separator pinned to the bottom of the cell | Full-width rows wasted the screen                 | low        |
| `web-frontend/modules/core/assets/scss/variables.scss`            | New `$dashboard-applications-breakpoint`                                                             | Single column below the width where counters clip | low        |

## Production hardening: security headers, source maps, inline CSS (2026-07-29)

Audit of the live deployment before go-live. Full findings, including the items
that need an admin-panel or Coolify change, are in
[docs/PRODUCTION_HARDENING.md](docs/PRODUCTION_HARDENING.md).

**The stylesheet was being inlined into every SSR response.** Nuxt does this by
default, which is right for a small stylesheet and wrong for a 1,870,576-byte
one: ~188 KB gzipped of uncacheable CSS on every document request, re-parsed
before first paint. Production was serving `entry.tn0RQdqM.css` at 0 bytes,
which is the tell. A verification build with `features.inlineStyles: false`
emits it as a real external file under `/_nuxt/`, where the existing
`immutable` cache header applies.

**Source maps were public.** `/_nuxt/DtultdTW.js.map` returned 200 with 4.2 MB
of original source. `sourcemap.client: 'hidden'` removes the pointer from all 81
chunks — verified 81 maps still emitted, 0 references remaining — but the files
stay on disk and stay fetchable, so Caddy also 404s `/_nuxt/*.map`. Scoped to
build output, so a user's own uploaded `.map` file still downloads.

**No security headers were sent at all.** HSTS, nosniff, Referrer-Policy and
Permissions-Policy added in the Caddyfile rather than at the edge, so they
survive a change of proxy. No global CSP: Nuxt serves inline bootstrap scripts,
so a guessed policy breaks the app silently. HSTS is a one-way door and is
called out as such in the doc.

**Clickjacking protection is scoped.** `frame-ancestors 'self'` on the signed-in
app, nothing on `/form/*` and `/public/*` so shared links stay embeddable.
`'self'` not `'none'` because the builder previews pages in a same-origin
iframe. Testing against a live Caddy — not just `caddy validate` — showed Django
sends its own `X-Frame-Options: DENY`, producing two conflicting values on
upstream errors; the `>` replace prefix fixes that.

**Login had no rate limiting.** Twelve consecutive failed logins returned 401
every time, never 429. Baserow's own throttle is off by default and counts
concurrency per user, not attempts per IP. A Traefik middleware on a
higher-priority router now covers the four credential endpoints at 5 req/s with
burst 20, keyed on `X-Forwarded-For` depth 1 — without that every request shares
one bucket and the site throttles as a whole.

Ruled out as causes of the reported self-reloading, by measurement: websockets
(101 upgrade in 0.44 s, anonymous auth succeeds), backend latency (0.28–0.36 s),
and TLS/redirects. Remaining candidate is container restarts, which cannot be
seen from outside; `docs/diagnose-production.sh` is read-only and collects it.

| File                                      | Change                                                                       | Reason                                                  | Merge risk |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------- | ---------- |
| `web-frontend/config/nuxt.config.prod.ts` | `inlineStyles: false`; client sourcemaps `hidden`                            | 1.8 MB CSS re-sent per request; 4.2 MB of source public | low        |
| `Caddyfile`                               | Baseline security headers; scoped frame-ancestors; 404 for build source maps | No headers at all; app framable; maps served            | medium     |
| `docker-compose.yml`                      | Traefik rate-limit router on the credential endpoints                        | No brute-force protection                               | low        |
| `docs/PRODUCTION_HARDENING.md`            | New: findings, and the settings only the operator can change                 | —                                                       | low        |
| `docs/diagnose-production.sh`             | New: read-only VPS diagnostics                                               | Self-reload cause needs server-side data                | low        |

## Dashboard charts — grouped aggregation service + chart widget (2026-08-03)

Upstream's four chart widgets (bar, line, pie, doughnut) are one `chart` widget
type living in the deleted `premium/`, backed by a premium
`local_baserow_grouped_aggregate_rows` service. Both are rebuilt from scratch
under `backend/src/arabase/` and `web-frontend/modules/arabase/`, keeping
upstream's **registry type names** so dashboards and templates that contain
charts import here instead of being skipped.

New models live in `arabase` (its first migration) rather than in
`contrib.integrations` / `contrib.dashboard`: a fork migration inserted into an
upstream app's sequence conflicts on every merge from upstream. Cross-app FKs to
`core.service`, `dashboard.Widget` and `dashboard.DashboardDataSource` work
unchanged, and both types register into the existing open registries from
`arabase/apps.py`, so no upstream Python file needed editing for the feature
itself. The four core-file edits below are registration and tooling only.

| File                                           | Change                                                                                                            | Reason                                                                                                                     | Merge risk |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py`  | Appended `ARABASE_CHART_MAX_BUCKETS` (default 100) under a "JADAWEL FORK SETTINGS" heading at the end of the file | A chart grouped by a high-cardinality field would otherwise ask the browser for one category per row                       | low        |
| `web-frontend/modules/arabase/module.js`       | Registers `./registryPlugin.js`, the `./locales` langDir, and `./assets/scss/dashboard_chart_widget.scss`         | Fork-owned file; the widget needs registry entries, its own strings, and styles                                            | none       |
| `web-frontend/scripts/check-locale-parity.mjs` | Added `modules/arabase/locales` to `localeDirectories`                                                            | The strict CI gate must cover the fork's own strings, which are deliberately _not_ added to upstream modules' locale files | low        |
| `backend/src/arabase/apps.py`                  | Registers the service type and widget type in `ready()`                                                           | Fork-owned file                                                                                                            | none       |

---

## Phase 2 — Rename the `baserow` code identifier to `jadawel` (2026-08-06)

**Context:** The fork had diverged far enough that carrying the upstream name inside the
code no longer described what this is. `docs/RENAME_TO_JADAWEL.md` holds the full plan,
the evidence behind it and the list of names deliberately left as `baserow`.

Every upstream-derived file under `backend/src/jadawel/` and `web-frontend/modules/`
was touched, so this section records the **classes** of edit rather than one row per
file. Nothing here changes behaviour; each is a rename plus the shims that keep the
old external names working.

| Change                                                                                                                                       | Reason                                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `backend/src/baserow` → `backend/src/jadawel`, 7,154 imports, 845 dotted strings, 629 deconstructed migration references                     | The Python package now matches the product. No database migration: every AppConfig sets `name` only, so `app_label` is still derived as `core`, `database`, …                                                                  |
| 53 `@app.task` decorators gained an explicit `name="baserow.…"`                                                                              | Celery derives a task name from the module path. Renaming the package would have renamed every task and stranded messages already queued in Redis                                                                              |
| `@baserow` → `@jadawel` alias, 3,749 frontend imports, 13 `runtimeConfig.public` keys                                                        | Declared in six places; all move together                                                                                                                                                                                      |
| 183 `BASEROW_*` environment variables → `JADAWEL_*`, plus `legacy_env.py`, the `env-remap.mjs` prelude and the `default_jadawel_env.sh` loop | Renaming an env var alone is silently destructive: an unset `BASEROW_JWT_SIGNING_KEY` falls back to `SECRET_KEY` and logs out every user with nothing in the log. All three runtimes accept the legacy spelling, new name wins |
| `/baserow` → `/jadawel` image paths, `jadawel.sh` entrypoint, `jadawel_docker_user`, compose service/volume names, the whole Helm chart      | The in-image filesystem prefix was baked into ~19 layers                                                                                                                                                                       |
| `BaserowFormula*.g4` → `JadawelFormula*.g4`, both parsers regenerated                                                                        | Generated output is byte-identical after name normalisation. `build.sh` now records the `typing.io` patch the repo always carried but never documented                                                                         |
| 18 email templates repointed at the renamed context keys                                                                                     | Django resolves a missing template variable to the empty string, so the share link and description had silently disappeared                                                                                                    |

**Left as `baserow` on purpose** — each is persisted state, a published contract, or
someone else's copyright, so renaming it would need its own migration rather than a
text edit: the 53 Celery task names and 7 `CELERY_TASK_ROUTES` keys, the OpenTelemetry
metric and attribute names, `local_baserow*` service type discriminators and
`LocalBaserow*` model (table) names, the `get_baserow_table_*` Postgres functions,
`core_settings.show_baserow_help_request`, the `jadawel_version_upgrade` notification
type, the `templates/baserow` loader directory, the `baserow` Postgres role and
database, `baserow.io` hostnames in fixtures, upstream's Docker Hub images and issue
URLs, and the `Baserow B.V.` copyright notice the MIT licence requires us to retain.

---

## Phase 3 — Finish the rename: schema, wire names and discriminators (2026-08-06)

**Context:** Phase 2 deliberately left every name that was persisted state or a
published contract, because renaming those needs a migration rather than a text edit.
With the application not yet live and no real data in the database, that constraint no
longer applies, so the remainder was renamed properly — with migrations, not by editing
history.

| Change                                                                                                                    | How                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 53 Celery task names and the 7 `CELERY_TASK_ROUTES` keys                                                                  | `baserow.*` → `jadawel.*`. Names stay explicit so a future module move cannot rename a task |
| OpenTelemetry metric and span names, and the `baserow.` attribute prefix                                                  | Now `jadawel.*`                                                                             |
| `templates/baserow` → `templates/jadawel`, and `tests/test_data/baserow` → `.../jadawel`                                  | Directory moves plus the 14 `template_name` strings                                         |
| `core_settings.show_baserow_help_request`                                                                                 | `RenameField` in `core/0117`                                                                |
| 29 `LocalBaserow*` models across `integrations`, `automation`, `builder`, `arabase`                                       | `RenameModel` in four hand-written migrations, so the tables are renamed in place           |
| 3 Postgres functions from `get_baserow_table_*`                                                                           | Recreated under `get_jadawel_table_*` and dropped, in `database/0211`                       |
| 13 `local_baserow*` service type discriminators                                                                           | Renamed in code and in the 1,103 occurrences inside the 63 bundled template JSON fixtures   |
| `baserow_version_upgrade` notification type, `ERROR_*_BASEROW_FIELD_NAME` API error codes, `RESERVED_BASEROW_FIELD_NAMES` | Renamed on both sides                                                                       |
| Postgres role, database and password defaults                                                                             | `baserow` → `jadawel` across settings, compose, CI and the documented examples              |

The historical migrations were **not** rewritten. Their `CreateModel(name="LocalBaserow…")`
operations and their `NNNN_…` dependency labels still read `baserow`, which is what makes
the `RenameModel` operations valid. Only their _import paths_ moved, because Python has
to be able to import them.

**Still `baserow`, permanently:**

- `Copyright (c) 2019-present Baserow B.V.` — the MIT licence requires the notice, and
  the Apache 2.0 notices from Jack Linke and Tal Shprecher likewise.
- Upstream's Docker Hub images (`baserow/baserow-pgautoupgrade`, `baserow/baserow-pg11`),
  its published Helm chart repository and its issue URLs — third-party coordinates.
- `baserow_premium` and `baserow_enterprise` in `test_fork_hygiene.py`, which asserts
  those proprietary packages are _not_ importable. Renaming them would void the guardrail.
- Sample data inside `backend/templates/*.json` (author emails, hosted URLs, form links)
  and `e2e-tests/fixtures/e2e-db.dump`, which are upstream's content.

---

## Dashboard grid layout — widget width/height and writable order (2026-08-06)

**Context:** The dashboard board becomes a 3-column grid with resizable, draggable
widgets (`wedage_kimi_plan.md`, Approach A). Two integers — `width` 1–3 and
`height` 1–3, default 3×2 so existing widgets keep today's full-width stacked
look — live on the base `Widget` model, so layout rides the existing CRUD API,
realtime broadcasts, undo/redo, trash and export/import instead of a fork-owned
sidecar model. Reorder reuses the fractional `order`, which the update endpoint
now accepts. Fork tests live in `backend/tests/arabase/test_widget_grid_layout.py`
(additive, not logged here). The fork-owned frontend pieces — the grid SCSS
partial, the `v-grid-sortable` directive and its order computations, the size
picker component and the frontend tests under
`web-frontend/test/unit/arabase/dashboard/` — are additive under
`web-frontend/modules/arabase/` and likewise not logged here.

| File                                                                           | Change                                                                                                                                                                                                                       | Reason                                                                                                                                                | Merge risk |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/dashboard/widgets/models.py`                      | `Widget.width`/`height` `PositiveSmallIntegerField` (validators 1–3, defaults 3 and 2)                                                                                                                                       | Grid cell spans must persist on the widget itself                                                                                                     | low        |
| `backend/src/jadawel/contrib/dashboard/migrations/0004_widget_width_height.py` | New migration adding the two fields                                                                                                                                                                                          | Fork-triggered additive migration                                                                                                                     | low        |
| `backend/src/jadawel/contrib/dashboard/api/widgets/serializers.py`             | `width`/`height` read-only in `WidgetSerializer`, optional in `CreateWidgetSerializer`, writable in `UpdateWidgetSerializer` alongside a new writable `order` `DecimalField`                                                 | Resize and drag-reorder go through the existing PATCH endpoint                                                                                        | low        |
| `backend/src/jadawel/contrib/dashboard/widgets/registries.py`                  | `WidgetType.allowed_fields` gained `"order"`, `"width"`, `"height"`                                                                                                                                                          | The single switch letting `update_widget` accept them (`extract_allowed`) and undo/redo capture them (`export_prepared_values`)                       | low        |
| `backend/src/jadawel/contrib/dashboard/widgets/handler.py`                     | `create_widget` pops `order` from kwargs before `extract_allowed`                                                                                                                                                            | With `order` now allowed, the service's default `order=None` kwarg would collide with the computed order (`got multiple values for keyword argument`) | low        |
| `backend/src/jadawel/contrib/dashboard/types.py`                               | `WidgetDict` gained `width: int`/`height: int`                                                                                                                                                                               | `get_property_names` reads the TypedDict annotations, so export/import round-trips the spans                                                          | low        |
| `backend/tests/jadawel/contrib/dashboard/api/widgets/test_widget_views.py`     | Expected response dicts gained `width`/`height`                                                                                                                                                                              | Existing assertions compare the full response body                                                                                                    | low        |
| `backend/tests/jadawel/contrib/dashboard/test_dashboard_application_types.py`  | Expected exported widget dicts gained `width`/`height`                                                                                                                                                                       | Existing assertions compare the full serialized dict                                                                                                  | low        |
| `web-frontend/modules/dashboard/components/WidgetBoard.vue`                    | Stacked `v-for` replaced by the 3-column CSS grid; wires the fork's `v-grid-sortable` (edit mode + `dashboard.widget.update` + viewport above `$dashboard-breakpoint`) with drop → fractional-order PATCH via `updateWidget` | Grid board and drag-reorder live in the upstream board component                                                                                      | low        |
| `web-frontend/modules/dashboard/components/widget/DashboardWidget.vue`         | Applies inline `grid-column: span N` / `grid-row: span N` from `widget.width`/`height`, falling back to 3×2 when absent                                                                                                      | Cell spans ride on each widget frame                                                                                                                  | low        |
| `web-frontend/modules/dashboard/components/widget/WidgetContext.vue`           | "Size" menu item gated on `dashboard.widget.update`, opening the fork's `WidgetSizeContext` 3×3 picker                                                                                                                       | Resize entry point lives in the upstream widget context menu                                                                                          | low        |
| `web-frontend/modules/dashboard/store/dashboardApplication.js`                 | `updateWidget` merges pending debounced values per widget (a drag's `order` plus a resize's `width`/`height` within 1 s both PATCH), flushes a different widget's pending update, commits the PATCH response back            | The cancel-and-replace debounce otherwise dropped a drag followed by a resize                                                                         | low        |
| `web-frontend/modules/dashboard/locales/en.json` and `ar.json`                 | `widgetContext.size` / `widgetContext.sizePreview` added to both locales                                                                                                                                                     | Size picker strings live next to `widgetContext.delete`; parity gate is strict                                                                        | low        |

---

## Phase 4 - Standalone: remove the remaining Baserow names (2026-08-06)

**Context:** With the fork treated as a standalone product, everything Phase 3 still
left reading `baserow` was renamed, except the attribution the licences require.

This pass found five breaks that Phase 2/3 had introduced and that a narrow test
selection had missed. The full backend suite had never been runnable in this fork -
six test files import the deleted `baserow_premium`/`baserow_enterprise` packages,
which aborted collection for all 8,000+ tests - so nothing was watching.

| Break                                                                                                                             | Effect if shipped                                              |
| --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 157 templates kept `baserow_template_version`; `handler.py` reads `jadawel_template_version` and **returns silently** when absent | template picker empty, nothing in the log                      |
| `supervisor.conf` reads `%(ENV_BASEROW_*)s`; `default_jadawel_env.sh` exports `JADAWEL_*`                                         | all-in-one image fails to start supervisor                     |
| webhooks emit `X-Jadawel-Event`/`-Delivery`; tests asserted `X-Baserow-*`                                                         | tests wrong, contract right                                    |
| code reads `Jadawel-View-Authorization`; tests sent `HTTP_BASEROW_VIEW_AUTHORIZATION`                                             | tests wrong, contract right                                    |
| `deploy/helm/jadawel/values.yaml` copyright flipped to `Jadawel B.V.` by `3c8cca0`                                                | **misattribution of Baserow's work; MIT terminates the grant** |

`backend/tests/arabase/test_fork_hygiene.py` now asserts every required attribution,
because two separate passes have rewritten one of them.

### Also renamed

- 11,663 strings across 161 bundled templates: author emails, sample URLs, the
  `Local Baserow` integration display name, `X-Baserow-*` sample webhook headers.
- 122 Postgres objects (55 constraints, 61 indexes, 6 sequences) whose names
  `RenameModel` left behind. Not cosmetic: Postgres quotes the constraint name back
  in every `IntegrityError`. Migration `integrations/0030` discovers and renames them
  rather than hard-coding, and is needed even on a from-zero database, because the
  history replays `CreateModel(name="LocalBaserow...")` before the rename.
- `e2e-tests/fixtures/e2e-db.dump` regenerated. It is a pre-migrated schema snapshot,
  so the Phase 3 model renames had already invalidated it. The generator recipe was
  itself broken - it dumped as user/db `baserow` against a container created as
  `jadawel`.
- The three import/export fixture zips: `local_baserow` inside `builder_export.zip`
  is a registry discriminator, so the schema JSON, its SHA-256 filename, the manifest
  checksums and the manifest signature all had to be rebuilt. Re-signed with
  `TEST_IMPORT_EXPORT_PRIVATE_KEY`, not a fresh key - the importer checks the public
  key against `ImportExportTrustedSource`.
- `.test_durations`: 2,928 stale entries dropped (223 test files no longer exist),
  41 keys renamed only where the renamed test was verified to exist.

### Permanently `baserow`

- `Copyright (c) 2019-present Baserow B.V.` in `LICENSE`, `deploy/helm/jadawel/values.yaml`
  and `circular_reference_checker.py`; `Copyright 2020, Jack Linke` (Apache-2.0 s4);
  `Copyright 2018 Tal Shprecher`. MIT's sole condition is that the notice is kept -
  dropping it ends the right to use the code at all.
- Upstream's Docker images (`baserow/baserow-pgautoupgrade`, `-pg11`) referenced in the
  PostgreSQL upgrade instructions, upstream issue URLs, and the fork's provenance line.
- `baserow_premium` / `baserow_enterprise`, upstream's real package names, which
  `test_fork_hygiene.py` asserts are _not_ importable.
- Historical migration filenames and their `CreateModel`/dependency strings, which the
  later `RenameModel` operations refer to by name.

`DatabaseRow*` contains the substring `baserow` (`data|baserow|perationtype`). A
case-insensitive rename corrupts it; the sweep matched case-sensitively to avoid this.

---

## Phase — Remove workspace AI keys, add public dashboard links (2026-08-09)

**Context:** Two product changes. (1) Generative AI provider credentials are no longer
configurable per workspace: they belong to the instance (env vars) or to an AI
integration's own `ai_settings`, and letting any workspace admin store third-party API
keys on the workspace was an entry point we do not want. (2) Dashboards gained the same
public link a form or grid view has — create, rotate, password-protect, revoke.

Almost all of the dashboard sharing feature is additive and therefore not listed here:
`backend/src/arabase/dashboard/share/`, `backend/src/arabase/api/dashboard_share/`,
`backend/src/arabase/migrations/0004_dashboard_share.py`, and
`web-frontend/modules/arabase/{plugins.js,routes.js,services,pages,dashboard}`. The
core files below are the seams those additions plug into.

| File                                                                        | Change                                                                                                                                                               | Reason                                                                                                                                             | Merge risk |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/api/workspaces/urls.py`                                | Dropped the `settings/generative-ai/` route and its view import                                                                                                      | Removes the API half of workspace-level AI keys; the URL now 404s                                                                                  | low        |
| `backend/src/jadawel/api/workspaces/views.py`                               | Deleted `WorkspaceGenerativeAISettingsView` and the imports it alone used (`validate_data`, `UpdateWorkspaceOperationType`, `get_generative_ai_settings_serializer`) | The view had no remaining route. `get_generative_ai_settings_serializer` itself stays — `contrib/integrations/ai` still uses it                    | low        |
| `backend/tests/jadawel/api/groups/test_workspace_views.py`                  | Removed `test_only_admin_can_list_generative_ai_settings` and `test_workspace_settings_override_global_generative_ai_settings`                                       | Both exercised the deleted endpoint. Replaced by `backend/tests/arabase/test_workspace_generative_ai_disabled.py`, which asserts the route is gone | low        |
| `web-frontend/modules/core/components/workspace/WorkspaceContext.vue`       | "Settings" menu item and `WorkspaceSettingsModal` now also require `hasWorkspaceSettings`                                                                            | Generative AI was the only registered `workspaceSettings` page; without the guard the menu opens an empty modal                                    | low        |
| `web-frontend/modules/core/components/workspace/WorkspaceSettingsModal.vue` | `mounted()` reads `registeredSettings[0]?.type ?? ''`                                                                                                                | The old `getOrderedList(...)[0].type` throws on an empty registry                                                                                  | low        |
| `web-frontend/modules/core/plugins.js`                                      | Added the `getAdditionalDashboardHeaderComponents(dashboard)` plugin hook                                                                                            | Lets the fork put the share menu in the dashboard header without the dashboard module importing from `arabase`                                     | low        |
| `web-frontend/modules/dashboard/components/DashboardHeaderMenuItems.vue`    | Renders the components returned by that hook                                                                                                                         | The other half of the same seam                                                                                                                    | low        |

The frontend half of the AI change needs no core edit: `registryPlugin.js` calls
`$registry.unregister('workspaceSettings', 'generative-ai')`, so
`GenerativeAIWorkspaceSettings.vue` and the two `workspace.js` service methods stay in
the tree as unreachable upstream code rather than becoming a deletion to re-apply.

---

## Phase — Split the Postgres client version from the embedded server (2026-08-17)

**Context:** The first real backup on CranL failed with _"pg_dump is version 15 but the
server is version 16"_. The all-in-one image derived both the embedded Postgres server
and the `postgresql-client` package from one `POSTGRES_VERSION=15`, but the database
being backed up is CranL's managed Postgres 16, which has nothing to do with the
embedded one. pg_dump refuses outright to dump a server newer than itself.

Raising `POSTGRES_VERSION` would have fixed the client and broken something worse: a
Postgres 16 server will not start on a PGDATA directory that 15 initialised, so every
existing embedded deployment would come up dead. The two versions are answering
different questions and are now separate.

Everything else is additive and not listed here: `client_binary()` and its tests live in
`backend/src/arabase/backup/`.

| File                           | Change                                                                                                                                                        | Reason                                                                                                       | Merge risk |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------- |
| `deploy/all-in-one/Dockerfile` | Added `POSTGRES_CLIENT_VERSION=18`; the base stage installs `postgresql-client-${POSTGRES_CLIENT_VERSION}` instead of `postgresql-client-${POSTGRES_VERSION}` | The client must be ≥ the server it dumps; the embedded server version is unrelated to that and must not move | med        |

`POSTGRES_VERSION=15` is deliberately unchanged — it still selects the embedded
`postgresql-15` and `postgresql-15-pgvector` in the `prod` stage.

18 rather than 16 because a newer pg_dump reads older servers without complaint and
refuses only newer ones, so the headroom is free and survives a managed-database upgrade.

One consequence worth knowing: the `prod` stage now has two clients installed, since
`postgresql-15` depends on `postgresql-client-15`. Debian's `/usr/bin/pg_dump` is
`pg_wrapper`, which picks a major from the default _cluster_ — the embedded one — so it
can still hand back the older binary. `arabase.backup.runner.client_binary()` therefore
resolves `/usr/lib/postgresql/*/bin/` itself and takes the highest major, rather than
trusting PATH.

---

## Phase — Bound workspace import archive expansion (2026-08-22)

**Context:** The workspace import API limited only the compressed upload size, then
fully decompressed `manifest.json` and every extracted entry into process memory before
schema or signature validation. A small, highly compressible ZIP could therefore kill a
web or Celery worker. The importer now rejects oversized archive metadata before parsing,
caps JSON inputs, and streams accepted entries to storage.

| File                                                                   | Change                                                                                                                                                                 | Reason                                                                                | Merge risk |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py`                          | Added configurable total-expanded and per-JSON workspace-import limits                                                                                                 | Let deployments align archive bounds with worker and storage capacity                 | low        |
| `backend/src/jadawel/core/import_export/handler.py`                    | Validate entry count, duplicate/encrypted entries and expanded sizes before parsing; use bounded JSON reads; stream extraction with a constant-time filename allowlist | Prevent ZIP-bomb memory, storage and CPU amplification before authenticity checks     | medium     |
| `backend/tests/jadawel/core/import_export/test_import_manifest.py`     | Added file-count, duplicate/encrypted-entry, signature, missing-schema, compressed-manifest, aggregate-size and application-JSON regression tests                      | Prove malformed or malicious archives fail before unbounded parsing or extraction     | low        |
| `backend/tests/jadawel/core/import_export/test_import_applications.py` | Added streamed-extraction and set-backed allowlist regression tests                                                                                                    | Prevent reintroduction of whole-entry `read()` buffering or quadratic filename checks | low        |

---

## Phase — Make OSS tests and dev profiling production-shaped (2026-08-23)

**Context:** Upstream's enterprise package supplies the only concrete user-source
type, but this OSS-only fork deliberately deletes that package. Generic upstream
test fixtures were still indexing an empty registry and failing instead of marking
the enterprise dependency unsupported. Separately, development settings enabled
django-silk for every request, which caused database contention and 500 responses
during concurrent authenticated testing even though production never enables Silk.

| File                                                                                                                                        | Change                                                                                                               | Reason                                                                                                                         | Merge risk |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `backend/src/jadawel/test_utils/fixtures/user_source.py`                                                                                    | Skip concrete user-source fixtures when the deleted provider is unavailable                                          | Keep the full OSS suite meaningful without recreating licensed enterprise code                                                 | low        |
| `backend/tests/jadawel/{api,core}/user_sources/conftest.py`                                                                                 | Mark provider-dependent user-source modules unsupported when the registry is empty                                   | Preserve generic source code while making the licensed test boundary explicit                                                  | low        |
| `backend/src/jadawel/test_utils/pytest_conftest.py`                                                                                         | Give the registry-stub fixture the same explicit OSS boundary                                                        | Avoid misleading index errors from an intentionally empty registry                                                             | low        |
| `backend/src/jadawel/test_utils/helpers.py`                                                                                                 | Make `AnyList` inherit from `list` instead of `dict`                                                                 | Keep response-shape assertions symmetric and compatible with Python 3.14 equality dispatch                                     | low        |
| `backend/src/jadawel/contrib/database/fields/field_helpers.py` and interesting-table tests                                                  | Remove the proprietary AI field from the all-field test matrix                                                       | Keep generic field coverage aligned with the OSS registry without importing `baserow_premium`                                  | low        |
| `backend/src/jadawel/contrib/database/api/rows/serializers.py`                                                                              | Represent empty row metadata as a free-form dictionary in OpenAPI examples                                           | Prevent `/api/schema.json` from crashing when the OSS row-metadata registry is empty                                           | low        |
| `backend/tests/jadawel/contrib/builder/test_builder_application_type.py`                                                                    | Expect builder imports to omit unavailable proprietary user sources and skip provider-only role remapping            | Verify the existing partial-import fallback while preserving the rest of the builder                                           | low        |
| `backend/tests/jadawel/contrib/database/api/views/test_view_views.py`                                                                       | Expect only the collaborative ownership type in API validation                                                       | Match the OSS ownership registry without restoring proprietary personal/restricted modes                                       | low        |
| `backend/tests/jadawel/contrib/{builder,database}/test_permissions_manager.py`                                                              | Remove the unavailable proprietary role manager from template-manager test settings                                  | Keep the tests focused on the core template permission manager                                                                 | low        |
| `backend/tests/jadawel/contrib/database/{api/webhooks/test_webhook_views.py,webhooks/test_webhook_validators.py}`                           | Stub outbound address probes and DNS in webhook tests                                                                | Make tests deterministic without weakening dedicated SSRF hostname and IP allow/deny coverage                                  | low        |
| `backend/tests/jadawel/contrib/database/mcp/test_mcp_table_tools.py`                                                                        | Include the fork's page-view tools in the enabled MCP inventory                                                      | Keep the static registry assertion aligned with additive Arabase tools                                                         | low        |
| `backend/tests/jadawel/contrib/integrations/local_jadawel/test_service_types.py`                                                            | Include the fork's upcoming-rows service in the dispatch inventory                                                   | Keep the static registry assertion aligned with additive Arabase services                                                      | low        |
| `backend/tests/jadawel/contrib/database/trash/test_database_trash_types.py`                                                                 | Omit the proprietary personal-view subcase when its ownership type is unregistered                                   | Preserve collaborative trash coverage without fabricating enterprise ownership behavior                                        | low        |
| `backend/tests/jadawel/contrib/database/view/{conftest.py,test_view_handler.py}`                                                            | Skip personal-ownership cases when only collaborative ownership is registered                                        | Preserve collaborative ordering coverage without relying on the deleted proprietary permission manager                         | low        |
| `backend/tests/jadawel/core/app_auth_providers/conftest.py`                                                                                 | Mark provider-dependent handler tests unsupported when the registry is empty                                         | Keep the licensed app-auth provider boundary explicit instead of failing on an empty registry                                  | low        |
| `backend/tests/jadawel/contrib/database/view/test_view_handler.py`                                                                          | Bound field-change cleanup at nine queries for both one and two fields                                               | Keep the N+1 regression check aligned with the smaller OSS registry                                                            | low        |
| `backend/tests/jadawel/core/test_basic_permissions.py`                                                                                      | Remove the deleted view-ownership manager from permission payload expectations                                       | Match the permission-manager list that OSS settings intentionally expose                                                       | low        |
| `backend/tests/jadawel/contrib/database/view/test_view_types.py`                                                                            | Mark personal-view import coverage with the existing ownership capability marker                                     | Skip only the unavailable proprietary ownership branch in OSS                                                                  | low        |
| `backend/src/jadawel/core/locale/ar/LC_MESSAGES/django.po` and core/user tests                                                              | Translate the default workspace name and account-email subjects; replace removed French coverage with Arabic         | Keep onboarding and account email flows aligned with the supported Arabic-first locale set                                     | low        |
| `backend/src/jadawel/core/locale/en/LC_MESSAGES/django.po`                                                                                  | Make English email subject branding explicit instead of depending on a stale compiled catalogue                      | Keep English and Arabic brand rendering deterministic after locale compilation                                                 | low        |
| `backend/tests/jadawel/api/import_export/sources/interesting_database_export.zip`                                                           | Remove six deleted proprietary AI fields and re-sign with the fixed test key                                         | Keep the signed full-import fixture representative of fields the OSS registry can actually import                              | low        |
| `backend/tests/jadawel/contrib/database/search/test_workspace_search_handler.py`                                                            | Treat five search queries as a regression ceiling and search a core select value instead of removed AI output        | Keep N+1 and field-search coverage aligned with the OSS interesting-table fixture                                              | low        |
| `backend/tests/jadawel/api/admin/users/test_users_admin_views.py`                                                                           | Treat seven queries as a regression ceiling, not an exact requirement                                                | Allow the OSS fork to perform fewer queries while still catching N+1 growth                                                    | low        |
| `backend/tests/jadawel/api/two_factor_auth/test_two_factor_views.py`                                                                        | Remove the deleted enterprise licence payload from OSS 2FA response expectations                                     | Match the actual core authentication contract without restoring enterprise serializers                                         | low        |
| `backend/tests/jadawel/contrib/builder/api/domains/test_domain_public_views.py`                                                             | Remove the deleted enterprise licence payload from public builder workspace expectations                             | Match the OSS public-builder serializer contract                                                                               | low        |
| `backend/tests/jadawel/api/users/test_user_views.py`                                                                                        | Exercise Arabic instead of removed French in API language updates                                                    | Keep user API tests aligned with the fork's Arabic/English-only contract                                                       | low        |
| `backend/src/jadawel/contrib/integrations/local_jadawel/service_types.py`                                                                   | Check automation row-write permissions against the target table workspace                                            | Published workflow clones have no application workspace; using that nullable scope silently discarded every mapped field value | low        |
| `backend/tests/jadawel/contrib/integrations/local_jadawel/service_types/test_upsert_row_service_type.py`                                    | Dispatch a mapped upsert through an integration whose application is null                                            | Prove published workflow clones retain mapped row values                                                                       | low        |
| `backend/src/jadawel/config/settings/dev.py`                                                                                                | Make django-silk profiling opt-in                                                                                    | Prevent profiler-induced failures from contaminating functional and load results                                               | low        |
| `web-frontend/modules/core/assets/scss/components/highlight.scss`                                                                           | Remove the superseded relative-position declaration                                                                  | Make the guided-tour RTL fix pass the enforced no-duplicate-properties rule                                                    | low        |
| `web-frontend/modules/core/plugins/posthog.js`                                                                                              | Load PostHog only when analytics is configured                                                                       | Keep the optional analytics SDK out of every default browser session                                                           | low        |
| `web-frontend/modules/core/pages/template.vue`                                                                                              | Replace the obsolete Nuxt 2 `asyncData` page hook with Nuxt 3 `useAsyncData` and preserve upstream HTTP failures     | Restore public template rendering without disguising backend outages as cacheable 404s                                         | low        |
| `web-frontend/modules/core/utils/error.js`                                                                                                  | Add shared page-error status normalization                                                                           | Keep Nuxt errors, HTTP client errors and network failures distinguishable                                                      | low        |
| `web-frontend/test/unit/core/utils/errors.spec.js`                                                                                          | Cover 404, upstream 5xx and network-error status normalization                                                       | Prevent public pages from collapsing every fetch failure into not-found                                                        | low        |
| `backend/src/jadawel/config/settings/e2e.py`                                                                                                | Delegate template startup to the fork's production catalog reconciler instead of importing the upstream default pair | Keep clean-stack browser tests aligned with the six-template production catalog                                                | low        |
| `web-frontend/modules/core/components/dashboard/DashboardApplication.vue`                                                                   | Render the relative creation time client-side                                                                        | Prevent second-boundary SSR hydration mismatches on newly created applications                                                 | low        |
| `web-frontend/modules/automation/applicationTypes.js`                                                                                       | Lazy-load the workflow template UI                                                                                   | Keep the Vue Flow editor out of unrelated initial page bundles                                                                 | low        |
| `web-frontend/modules/builder/realtime.js`                                                                                                  | Ignore `page_created` events when their builder is no longer in the application store                                | Prevent delayed WebSocket events from dereferencing a deleted builder during navigation or cleanup                             | low        |
| `web-frontend/modules/core/assets/scss/components/{auth,datepicker,tree}.scss` and `builder/elements/ab_components/ab_datetime_picker.scss` | Replace physical dimensions and block margins/borders with logical properties                                        | Keep desktop layout direction-safe and make Stylelint warning-free                                                             | low        |
| `web-frontend/.stylelintignore`                                                                                                             | Exclude Nuxt production output directories                                                                           | Keep lint deterministic after a local or CI production build creates symlinked server dependencies                             | low        |

## Phase — Harden dashboard sharing and Context lifecycle (2026-08-23)

| File                                                 | Change                                                                                                | Reason                                                                                                                                        | Merge risk |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/core/plugins/clientHandler.js` | Normalize trailing slashes before appending `/api`                                                    | Prevent production origins such as `https://jadawl.site/` from producing a `//api` request path                                               | low        |
| `web-frontend/modules/core/components/Context.vue`   | Keep a stable raw HTMLElement for geometry/listener registration and make listener cleanup idempotent | Prevent stale resize callbacks or Vue root transitions from calling geometry methods on a comment node; preserve edge flipping in LTR and RTL | medium     |
| `web-frontend/package.json`                          | Run ESLint from the frontend package instead of its parent directory                                  | Prevent ESLint from resolving Ubuntu's system parser packages, whose placeholder version breaks the full lint gate                            | low        |

## Phase — Bound and parallelize production SSR (2026-08-24)

**Context:** The production-shaped load gate showed that the backend remained below
436 ms p95 with 60 concurrent clients, while a single Nitro process serialized SSR
login rendering and made both `/login` and the otherwise-lightweight `/_health` route
wait for more than five seconds. Nitro's cluster preset fixes that head-of-line
blocking, but its default is one worker per visible host CPU, which is unsafe when a
container can see more CPUs than its 4 GB CranL memory allocation can support. The
portable image therefore defaults to one; CranL and the production load gate explicitly
run the measured two-worker profile. The two-worker load test also exposed Gunicorn's
two-second keep-alive racing Node 24's five-second pooled sockets: roughly 0.2% of SSR
login requests reused a connection while the backend closed it and returned a 500.

| File                                          | Change                                                                       | Reason                                                                                                                               | Merge risk |
| --------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `web-frontend/config/nuxt.config.prod.ts`     | Build the production server with Nitro's `node-cluster` preset               | Use more than one CPU for concurrent SSR document requests                                                                           | medium     |
| `web-frontend/env-remap.mjs`                  | Default `NITRO_CLUSTER_WORKERS` to one while preserving an explicit override | Prevent host CPU count from turning into an unbounded number of full Nuxt worker processes; resource-aware deployments opt into more | low        |
| `backend/docker/docker-entrypoint.sh`         | Set Gunicorn's backend keep-alive to ten seconds                             | Keep backend sockets open beyond Node's five-second pool lifetime and prevent intermittent SSR `socket hang up` responses            | low        |
| `backend/src/jadawel/config/settings/base.py` | Select `project-management-en` as the default application template           | Keep the template modal usable after the hosted catalog prunes the former `project-tracker` default                                  | low        |

## Phase — Render shared dashboard aggregates (2026-08-24)

**Context:** Public dashboard serializers deliberately omit table, field, filter and
aggregation configuration. Summary widgets still passed that reduced service object to
the private aggregate formatter during SSR, which dereferenced the missing field and
turned otherwise-successful shared dashboard requests into HTTP 500 responses.

| File                                                                    | Change                                                                                   | Reason                                                                                  | Merge risk |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/integrations/localJadawel/serviceTypes.js`        | Return the already-serialized aggregate result when private formatting context is absent | Render anonymous dashboard summaries without exposing private data-source configuration | low        |
| `web-frontend/test/unit/integrations/localJadawel/serviceTypes.spec.js` | Cover reduced public services and fully configured private services                      | Prevent the SSR crash from returning while preserving private result formatting         | low        |

## Phase — Default to white and localize English template samples (2026-08-24)

**Context:** The interface theme picker listed the green sage palette first and used it
for users without a stored preference. The English template catalog also mixed a Saudi
product context with generic or US-oriented sample records. White now leads the theme
row and is the true fallback, while English table and field labels keep their language
and the records use Saudi personal names transliterated into English plus Saudi
organisations, phone numbers, locations, payment methods, finance terms and operating
examples.

| File                                                                                                                                          | Change                                                                                                                                                                            | Reason                                                                                                                                                                 | Merge risk |
| --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `web-frontend/modules/core/utils/interfaceThemes.js`                                                                                          | Put white first, set it as the default, and keep sage second                                                                                                                      | Make the neutral workspace the first-run experience without removing the green option                                                                                  | low        |
| `backend/templates/{performance-reviews,project-management-en,saudi-budget-consolidation-en}.json`                                            | Replace generic and US-oriented records with English-transliterated Saudi names and Saudi sample context; remove invalid average footers from the two link-derived count formulas | Make every approved English template feel locally relevant while preserving English schemas, and keep the performance preview aggregation endpoints from returning 500 | low        |
| `backend/src/arabase/template_catalog.py`                                                                                                     | Include bundled export hashes in the current-catalog check                                                                                                                        | Refresh edited template previews instead of treating matching slugs and categories as current forever                                                                  | low        |
| `web-frontend/test/unit/core/{utils/interfaceThemes.spec.js,components/appUtilities.spec.js}` and `backend/tests/arabase/test_*_template*.py` | Cover theme order/default, English schema language, Saudi records, installability and content refresh                                                                             | Keep both visible changes and the catalog refresh path regression-tested                                                                                               | low        |

## Phase — Isolate MCP protected-value token storage (2026-08-30)

**Context:** Protected MCP responses need short-lived opaque handles whose bindings
and keyed fingerprints are stored outside the relational database. These settings
are private backend configuration and therefore cannot live exclusively in the
additive Arabase module.

| File                                          | Change                                                       | Reason                                                                                                                                    | Merge risk |
| --------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/config/settings/base.py` | Added private MCP protection Redis and HMAC keyring settings | Give the additive Arabase protection boundary a fail-closed, deployment-configurable token vault without exposing secrets to the frontend | low        |

| `backend/src/jadawel/contrib/database/rows/actions.py` | Skip content-bearing generic row action history and webhook events while a protected MCP mutation is active | Keep plaintext protected values out of durable action/webhook payloads; the Arabase boundary records a content-blind mutation audit instead | medium |

## Phase — Expand MCP client setup guidance (2026-08-31)

| File                                                                                                                 | Change                                                                                                 | Reason                                                                                                                                                             | Merge risk |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `web-frontend/modules/core/components/settings/McpEndpoint.vue` and `web-frontend/modules/core/locales/{ar,en}.json` | Replace the Windsurf setup tab with Codex CLI guidance and add a localized prompt for other AI clients | Make the default setup choices match the supported Jadawel workflows while giving any MCP-capable agent enough safe, endpoint-specific context to configure itself | low        |
| `web-frontend/modules/core/components/settings/McpEndpoint.vue`                                                      | Normalize trailing slashes before appending the MCP route                                              | Keep the displayed and copied credential URL directly usable when CranL's public backend URL ends in `/`                                                           | low        |

## Phase — Keep sidebar modals usable on mobile (2026-09-01)

| File                                                          | Change                                                                   | Reason                                                                                                                                                       | Merge risk |
| ------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `web-frontend/modules/core/assets/scss/components/modal.scss` | Stack sidebar modals and remove fixed sidebar/content sizing below 720px | Prevent the authenticated Arabic/English settings modal from creating an internal horizontal strip at 390×844 while preserving the desktop two-column layout | low        |

## Phase — Drop the notification panel below the content header (2026-09-06)

User-reported: opening the bell's notification panel covered the whole content
header, hiding search and settings the moment it opened. Upstream's
`inset-block: 8px` made the panel span the full viewport because the bell lived
in the sidebar, where a full-height drawer reads as a sidebar panel. This fork
moved the bell into the content header (2026-07-28), so the drawer now hangs
from a control in a 51px bar and must not swallow it. Anchored at
`inset-block: 59px 8px` — header height plus the same 8px gap the other edges
keep. The taller 74px workspace-home header centres its controls (bell spans
22–52px), so they stay clear without a per-page exception.

| File                                                                       | Change                                       | Reason                                                          | Merge risk                                                      |
| -------------------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- |
| `web-frontend/modules/core/assets/scss/components/notification_panel.scss` | `inset-block: 8px` → `inset-block: 59px 8px` | The panel opened over the header that hosts the bell opening it | low — upstream touches this rule only if it redesigns the panel |

## Phase — Fix the onboarding preview highlight crash (2026-09-06)

User-reported: a fresh user's onboarding (first login after signup) crashed
the database step's preview with `TypeError: Cannot read properties of null
(reading 'top')` at `Highlight.vue:117`. Two causes compounded. The sidebar
simplification (2026-07-28) removed the per-type application groups whose
wrapper carried `data-highlight="applications-${type}"`, but the database
onboarding step still asked for `applications-database` — a selector that
matches nothing, so `Highlight.update()` received an empty element list. And
`getCombinedBoundingClientRect([])` returns `null`, whose `.top` the un-guarded
updater then read.

| File                                                                                                                                                    | Change                                                                                               | Reason                                                                                                                                                     | Merge risk                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `web-frontend/modules/database/onboardingTypes.js`                                                                                                      | `highlightDataName: 'applications-database'` → `'applications'`                                      | The flat sidebar still tags its applications section with `data-highlight="applications"`; upstream's per-type group element no longer exists in this fork | low — reverts to upstream's pre-grouping value |
| `web-frontend/modules/core/components/Highlight.vue`                                                                                                    | Guard `update()` when no elements match; fall back to a centered box                                 | Port of upstream's own fix — a stale selector crashed the whole preview instead of degrading                                                               | low — matches upstream develop verbatim        |
| `web-frontend/test/unit/core/components/highlight.spec.js` and `web-frontend/test/unit/database/components/onboarding/databaseAppLayoutPreview.spec.js` | Cover the no-match fallback and pin the highlight target to an element the preview's sidebar renders | Both went red on the original crash; keeps the selector and the sidebar in lock-step                                                                       | low                                            |

## Security maintenance (2026-09-07)

| File                                          | Change                                                                | Reason                                                                                                                   | Risk                                                            |
| --------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `backend/src/jadawel/config/settings/base.py` | Parse `JADAWEL_INTEGRATIONS_ALLOW_PRIVATE_ADDRESS` with `str_to_bool` | The strings `false`, `off`, and `0` previously enabled private-network requests and bypassed Advocate address validation | Low; intentional private access must use an explicit true value |

## Phase — Gate public links for suspended organization workspaces (2026-09-08)

| File                                                                                                      | Change                                                                                                   | Reason                                                                                                                                             | Risk                                                         |
| --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `backend/src/jadawel/contrib/database/views/handler.py`, `backend/src/arabase/dashboard/share/handler.py` | Call the optional organization public-workspace policy before resolving a public view or dashboard share | Organization suspension must disable existing public links without deleting their share configuration; unmanaged workspaces keep the upstream path | Low; optional imports are guarded by installed-app detection |

## Phase — Reject legacy membership mutations for managed workspaces (2026-09-08)

| File                                  | Change                                                                                        | Reason                                                                                                                                                                 | Risk                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `backend/src/jadawel/core/handler.py` | Invoke an optional plugin callback before creating or accepting a legacy workspace invitation | Bound organization workspaces must use organization invitations so seat locking, roles and audit records cannot be bypassed; unmanaged workspaces retain the core flow | Low; callback is optional and only installed plugins implement it |

## Follow-up remediation — translatable export errors and cancel cleanup (2026-09-14)

Implements Phase 3 (localized dimension failures, cancellation cleanup) of
`docs/NEW_FEATURES_REMEDIATION_FOLLOWUP_PLAN.md`.

| File                                                                                                          | Change                                                                                                                                                             | Reason                                                                                                                                                      | Merge risk |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `backend/src/jadawel/contrib/database/export/handler.py`                                                      | Runs the export job under the exporting user's language (`translation.override`); deletes the partial storage file when a job is cancelled after rows were written | Dimension-limit errors are gettext strings so Arabic/English users get the right message; a cancelled export must not leave a downloadable partial workbook | low        |
| `backend/src/jadawel/contrib/database/api/views/grid/utils.py`, `grid/views.py`, `views/view_aggregations.py` | Ruff isort/import hygiene only (no behavior change)                                                                                                                | Phase 5 lint gate of the follow-up plan                                                                                                                     | none       |

The XLSX/ODS exporter itself stays under `backend/src/arabase/export/` (additive);
its dimension-limit exception now uses `gettext_lazy`, and the Arabic catalogue
`backend/src/arabase/locale/ar/LC_MESSAGES/` supplies the translations (the `.mo`
is committed; regenerate it after editing the `.po` — msgfmt is not installed in
the image, compile per PATCHES conventions).

## Phase — Apply the interface theme before the first paint (2026-09-16)

**Context:** Two theme defects came from the same place: the document was themed
after hydration instead of before the first paint. `head.js` declared
`data-interface-theme="white"` as a static html attribute, and unhead re-applies
every attribute it manages on hydration (`$el.getAttribute(k) !== v →
setAttribute`), so it reset the attribute to `white` right after the client
plugin had set the stored theme on it. The custom properties kept the stored
palette while the `[data-interface-theme='white']` chrome rules kept applying, so
a stored theme looked unapplied until the user re-picked it from the menu. And
because SSR cannot read localStorage, the first frame painted in the stylesheet's
own `var()` fallbacks — still the sage-derived greens — which is the green flash
on every refresh.

| File | Change | Reason | Merge risk |
| ---- | ------ | ------ | ---------- |
| `web-frontend/modules/core/head.js` | Drop the static `htmlAttrs['data-interface-theme']`; add an inline, synchronous head script that applies the stored theme | unhead must not own that attribute, and the theme has to be on the document before the body is parsed | low |
| `web-frontend/modules/core/utils/interfaceThemes.js` | Extract `getInterfaceThemeVariables` / `INTERFACE_THEME_VARIABLES`; add `getInterfaceThemeBootScript` | One source for the custom properties, shared by the runtime apply and the pre-paint script, so the two cannot drift | low |
| `web-frontend/modules/core/assets/scss/components/{layout,sidebar,card,dashboard}.scss` | Retarget the `var()` fallbacks for sidebar/content/raised/hover backgrounds from the sage-derived values to the white theme's | The fallbacks are what paints when the properties are unset; they were green | low |
| `web-frontend/test/unit/core/{utils/interfaceThemes.spec.js,gridHeaderTheme.spec.js}` | Cover the boot script, assert the head never declares the attribute, and scan every `var()` fallback against the default theme | Both defects are regressions a unit test can hold; the fallback scan is what keeps green from creeping back in | low |

The client plugin `plugins/interfaceTheme.client.js` stays. It is now a
correction rather than the primary path: it repairs storage that names a removed
theme, and still applies the theme if the head script could not run.
