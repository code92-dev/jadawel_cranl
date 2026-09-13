# Upstream Baserow 2.3 changes after 2.2.2

Research date: 2026-09-13

## Scope and sources

This note describes upstream changes between the `2.2.2` baseline and the Baserow
`2.3.x` release family. It does **not** claim that these changes are present in
Jadawel; that requires a separate source audit of this repository.

Primary sources:

- [Baserow 2.3 product release notes](https://baserow.io/blog/baserow-2-3-release-notes)
- [GitHub release 2.3.0](https://github.com/baserow/baserow/releases/tag/2.3.0)
- [GitHub release 2.3.1](https://github.com/baserow/baserow/releases/tag/2.3.1)
- [GitHub release 2.3.2](https://github.com/baserow/baserow/releases/tag/2.3.2)
- [GitHub release 2.3.3](https://github.com/baserow/baserow/releases/tag/2.3.3)
- [GitHub release 2.2.2](https://github.com/baserow/baserow/releases/tag/2.2.2)

The upstream blog announced 2.3 on 2026-07-08. GitHub published `2.3.0` and
`2.3.1` on 2026-07-10, `2.3.2` on 2026-07-15, and `2.3.3` on 2026-07-21.

## Major user-facing changes in 2.3.0

### Database Builder

- **Live presence and cell editing:** editors can see who is viewing a table and
  which cells other users are editing. WebSocket reconnect/recovery was also
  improved. Sources: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#real-time-cell-editing),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **Expanded Group By:** groups can be collapsed and expanded, rows can be created
  inside groups, per-group aggregations are shown, group fields can be reordered,
  and a view can group by as many as five fields. Source:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#improved-group-by-views).
- **Excel/ODS import:** new tables can be created from `.xlsx`, `.xls`, or `.ods`;
  users can select a workbook sheet and whether the first row contains headers.
  Upstream also added importing into an existing table from its sidebar context
  menu. Sources: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#import-excel-files-to-create-new-tables),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **View and data handling:** sort and Group By rules gained drag-and-drop ordering;
  Kanban stacks gained sorting; synced tables gained an option to retain rows
  deleted or hidden at the source; related-record changes update formula, lookup,
  and link cells in real time; and long-running imports/syncs gained progress and
  cancellation handling. Sources: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#additional-improvements),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **Smaller database additions:** a `starts with` text filter, a clear button for
  view search, configurable omission of Row ID/primary-field columns from exports,
  and better restricted-view defaults/filter feedback. Source:
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).

### Automations and integrations

- **JavaScript execution:** a Code service/node can run JavaScript in Automations
  and Application Builder. Baserow states this is an Advanced/Enterprise feature.
  Source: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#code-execution-node).
- **Spreadsheet readers:** workflows and applications gained Read CSV and Read
  XLS/XLSX actions, including selecting an Excel worksheet. Source:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#read-csv-and-excel-files).
- **Batch row actions:** workflow/application actions can create or update up to
  1,000 rows in one action; the GitHub release also lists batch delete support.
  Sources: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#batch-row-operations),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **More precise and reusable workflows:** a trigger can react only when selected
  fields change; a Start workflow action can invoke another workflow from an
  automation or application; and a Manual trigger supports reusable workflows that
  do not start automatically. Sources:
  [specific-field trigger](https://baserow.io/blog/baserow-2-3-release-notes#trigger-workflows-when-specific-field-values-are-updated),
  [Start workflow](https://baserow.io/blog/baserow-2-3-release-notes#start-workflows-from-other-workflows-or-applications),
  [Manual trigger](https://baserow.io/blog/baserow-2-3-release-notes#manual-trigger).
- **Workflow diagnostics:** node history exposes executed steps, outputs, nested
  iterations, and the exact failing node. The release also records history
  performance and retention work. Sources:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#node-history),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **Product status:** Baserow declared Automation Builder out of beta and introduced
  automation credits on Baserow Cloud. This is a Cloud commercial-policy change,
  not evidence of a self-hosted runtime limit. Source:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#automation-credits-in-baserow-cloud).

### Application Builder and expressions

- **Undo/redo and trash:** pages and elements gained undo, redo, and deletion
  recovery; the product notes specify a three-day restore window. Sources:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#undo-redo-and-restore-deleted-elements),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **Responsive layouts:** Columns gained layout presets, custom widths, and
  per-device stacking; Menu gained responsive burger variants; element
  drag-and-drop behavior was improved. Sources:
  [column layouts](https://baserow.io/blog/baserow-2-3-release-notes#more-flexible-column-layouts),
  [burger menus](https://baserow.io/blog/baserow-2-3-release-notes#responsive-burger-menus).
- **Duration and formula support:** duration values became usable in applications,
  duration arithmetic/formatting was expanded, and the runtime expression set added
  `number_format()`, `abs()`, `null()`, `to_duration()`, `to_datetime()`,
  `to_json()`, `from_json()`, and `range()`. The product notes call the formatting
  function `format_duration()` while the GitHub release calls it
  `duration_format()`; source inspection is required before porting that exact API
  name. Sources: [product notes](https://baserow.io/blog/baserow-2-3-release-notes#duration-inputs-and-formula-improvements),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).

### Administration, security, and platform

- Instance administrators can view users' 2FA status and remove a user's 2FA when
  recovery is needed. Workspace/application membership management was extended to
  Builder applications, Automations, and Dashboards. Sources:
  [product notes](https://baserow.io/blog/baserow-2-3-release-notes#additional-improvements),
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- Frontend infrastructure moved to **Nuxt 4**, caching became enabled by default,
  and the backend was updated to Python 3.14.6 to address a memory leak. The release
  also lists dependency security updates and several real-time, search-index, import,
  sync, query-performance, and memory fixes. Source:
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0).
- **Breaking API behavior:** reordering a row no longer changes its `updated_on`
  value, so Last Modified fields and formulas tied to `updated_on` are not recomputed
  merely because the row moved. Source:
  [2.3.0 release](https://github.com/baserow/baserow/releases/tag/2.3.0#breaking-api-changes).

## Additions and fixes in later 2.3 patches

- `2.3.1`: remembers the last-opened comments/history tab in the row editor; adds
  fixed positioning for Application Builder headers/footers; and adds a configurable
  maximum length for text-based field values. Source:
  [2.3.1 release](https://github.com/baserow/baserow/releases/tag/2.3.1).
- `2.3.2`: adds Group By directly from a field's column menu and fixes Advanced-plan
  access to Code and XLS actions, plus data-sync, grouping, periodic-update, and N+1
  query issues. Source:
  [2.3.2 release](https://github.com/baserow/baserow/releases/tag/2.3.2).
- `2.3.3`: shows anonymous public-view visitors in the presence bar; adds links and
  rich formatting to form/field descriptions; adds private-network blocking controls
  for URL-based data sync and configurable SSO URLs; and fixes deactivated-user
  impersonation, memory, workspace-manifest validation, and other issues. Source:
  [2.3.3 release](https://github.com/baserow/baserow/releases/tag/2.3.3).

## Porting implications (inference, not release-note claims)

- Excel import is connected to broader 2.3 import/job-management work, so copying
  only a menu component is unlikely to be sufficient; importer backend handlers,
  task progress/cancellation, dependencies, API types, translations, and frontend
  registration should be checked together.
- A full 2.3 merge is higher risk than an isolated feature port because Nuxt 4,
  caching defaults, Python/runtime fixes, migrations, WebSocket behavior, and the
  `updated_on` semantic change can affect the whole deployment.
- The Code execution feature is not a suitable direct port to this OSS-only fork
  without first resolving licensing and runtime-isolation requirements; upstream
  identifies it as an Advanced/Enterprise capability.
- Patch releases through `2.3.3` contain correctness and security hardening. If the
  target is “upstream 2.3,” auditing against `2.3.3` is safer than stopping at
  `2.3.0`.

## Jadawel source audit

Audited against Jadawel commit `e14f16335619` on 2026-09-13. The frontend still
declares version `2.2.2` in `web-frontend/package.json`. This table checks concrete
registrations, components, models, migrations, and configuration; it does not infer
availability from the version string alone.

| Upstream 2.3 capability | Jadawel status | Local evidence |
|---|---|---|
| Excel/ODS table importer | Missing | The importer registry in `web-frontend/modules/database/plugin.js` registers only CSV, paste, XML, and JSON; there is no `TableExcelImporter.vue` or `xlsx` dependency. |
| Live user/cell-edit presence | Missing | `backend/src/jadawel/ws/` has no upstream 2.3 `presence.py`, `models.py`, `realtime_events.py`, or `types.py`, and no presence UI was found. |
| Collapsible Group By, per-group aggregations, five-level cap, and drag reordering | Missing | Current `ViewGroupByContext.vue` is the 2.2-style field picker; it has no `MAX_GROUP_BYS`, collapse controls, drag wrapper, or `GridViewGroupByAggregation`. Basic Group By remains available. |
| Kanban sorting | Equivalent present | The additive fork implementation declares `can_sort = True` in `backend/src/arabase/kanban/view_types.py` and `canSort()` in `web-frontend/modules/arabase/kanban/viewType.js`. This was implemented independently in Jadawel, not imported as the upstream paid Kanban module. |
| Builder undo/redo and page/element trash | Missing | No upstream 2.3 element/page action or trash types are present under `backend/src/jadawel/contrib/builder/`; only the older domain trash type exists. |
| Responsive Column presets and burger Menu | Missing | The current Column element only calculates equal percentage widths; no column stacking/preset model fields or burger style/component were found. |
| Workflow node history | Present from baseline | `AutomationNodeHistory` and `NodeHistory.vue` exist locally, but they also exist in the official `2.2.2` tag, so this is not evidence of a 2.3 port. |
| CSV reader, batch-row actions, selected-field trigger, Start workflow, Manual trigger | Missing | No corresponding service types, node types, models, or migrations were found in backend or frontend registries. |
| JavaScript Code node and XLS workflow reader | Missing by fork policy | Upstream implements these under `enterprise/`; Jadawel deliberately excludes the Premium and Enterprise packages. This is distinct from the core/free Excel table importer. |
| New runtime expressions (`to_json`, `from_json`, `number_format`, `null`, `to_duration`, `to_datetime`, `range`) | Missing | The upstream 2.3 runtime formula type registrations are absent. Existing database formula and aggregation code with similar names is not the same runtime-expression feature. |
| Admin display/reset of user 2FA | Missing | The admin API and admin user components contain no upstream 2.3 2FA status field or disable endpoint/modal. User-managed 2FA still exists. |
| Nuxt 4 | Missing | `web-frontend/package.json` pins Nuxt `3.21.10`. |
| Default general cache TTL | Missing | `JADAWEL_CACHE_TTL_SECONDS` defaults to `0`; upstream 2.3 changed its equivalent default from `0` to `120`. |
| Python 3.14.6 memory fix | Partial/older | Jadawel already uses Python 3.14, but its image is pinned to `3.14.3`, not the upstream 2.3 fix version `3.14.6`. |
| Moving rows no longer changes `updated_on` | Missing | Local `rows/handler.py` still saves both `order` and `updated_on` when moving a row, matching upstream 2.2.2 behavior. |

The closest current summary is therefore: **Jadawel is not partially upgraded to
upstream 2.3 as a release.** It has a few overlapping or independently implemented
capabilities, while most 2.3 features and semantic changes remain absent.
