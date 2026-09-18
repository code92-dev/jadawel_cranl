# Table-level access plan — invite someone to one table, not the whole workspace

## Status (2026-09-18)

| Packet | State |
|---|---|
| 1 — backend foundation (`GUEST` role, two models, migration `0017_table_access_grants`) | **Implemented** |
| 2 — `table_grants` permission manager (deny-by-default, listings, permissions object) | **Implemented** |
| 3 — invitation and grant API under `/api/arabase/workspace/<id>/table-access/` | **Implemented** |
| 4 — frontend: Table access settings tab, GUEST label, ar+en strings | **Implemented** |
| 5 — linked-field hiding (three core patches, logged in `PATCHES.md`) | **Implemented** |
| 6 — hardening (search, realtime, tokens, trash, export; organization workspaces) | **Partly done** — see below |

Verified:

- `pytest tests/arabase/test_table_access.py` → **20 passed**
- `pytest tests/arabase` → **423 passed, 1 skipped**
- `pytest tests/jadawel/contrib/database/api/{rows,fields}` → **475 passed**, and
  batch rows + grid views rerun → **230 passed**, against the packet 5 core patch
- `vitest test/unit/arabase/tableAccess.spec.js` → **13 passed**
- `ruff check` / `ruff format --check` on the new and patched Python → clean
- `prettier` and `stylelint` on the new frontend files → clean
- `yarn locale:check --strict` → 3870/3870, 0 missing

Still open in packet 6: workspace-wide search, `broadcast_to_group` metadata
events, and export/webhook paths have no guest-specific test yet; guests in
organization-managed workspaces are refused (covered by a test) rather than
supported.

## Decisions taken

| Question | Decision |
|---|---|
| What a guest can do | Two grant levels chosen per invite: **Viewer** (read rows and views) and **Editor** (also create/update/delete rows, never schema) |
| Scope of one invitation | **One or more tables**, named explicitly |
| Who can receive a grant | **Outsiders invited by email**; existing members keep their current workspace role untouched |
| Linked data the guest was not granted | **Hide the fields** — link-row, lookup and formula fields that read through to an ungranted table disappear from the guest's field list, rows and exports |

## What exists today

Access is workspace-wide and nothing narrower exists:

- `WorkspaceInvitation` (`backend/src/jadawel/core/models.py:360`) carries a
  single `permissions` string and is unique per `(workspace, email)`.
- Accepting it calls `CoreHandler.accept_workspace_invitation`
  (`backend/src/jadawel/core/handler.py:1279`), which adds a `WorkspaceUser`
  with that permissions string, fires `workspace_invitation_accepted`, then
  deletes the invitation.
- `permissions` is a plain `CharField(max_length=32)` with no `choices`, and
  the API serializer (`backend/src/jadawel/api/workspaces/invitations/serializers.py`)
  does not constrain it either.
- The fork already added a third role this way: `ViewerRolePermissionManagerType`
  (`backend/src/arabase/permissions/viewer_role.py`) stores `VIEWER` on that same
  field, denies view-configuration mutations, and is inserted before `basic` in
  `settings.PERMISSION_MANAGERS` from `ArabaseConfig.ready()`
  (`backend/src/arabase/apps.py:108-123`). No schema change, no core edit.
- Upstream's per-scope RBAC lived in `baserow_enterprise`, which this fork
  deletes; `role` and `write_field_values` are removed from `PERMISSION_MANAGERS`
  at `backend/src/jadawel/config/settings/base.py:1359-1360`.
- `docs/PAYMENT_ORGTEAM_PLUGINS_PLAN.md:268` explicitly deferred "per-table role
  builders" out of the billing/organizations v1, so no prior design constrains us.

## Constraints the architecture imposes

These are not choices; they follow from the code.

1. **A table guest is still a workspace member.**
   `WorkspaceMemberOnlyPermissionManagerType`
   (`backend/src/jadawel/core/permission_manager.py:157-283`) denies every
   operation to an actor with no `WorkspaceUser` row. "Table-only access"
   therefore means *a workspace member whose visible surface is narrowed to some
   tables*, not a new kind of actor. The guest will see the workspace in their
   sidebar; everything inside it has to be filtered.

2. **Hiding the rest of the sidebar needs no core edit.** Application listing
   (`backend/src/jadawel/core/handler.py:1634`) and table listing
   (`backend/src/jadawel/contrib/database/api/tables/views.py:143,208`) both run
   through `CoreHandler().filter_queryset`, which every permission manager can
   narrow via `PermissionManagerType.filter_queryset`.

3. **Scope resolution is already available.** `ObjectScopeType`
   (`backend/src/jadawel/core/registries.py:828`) exposes `get_parents(context)`,
   so any check context — a view, a field, a row, a filter — can be walked up to
   the table it belongs to in one call.

4. **The invitation flow has fork hooks already.** `create_workspace_invitation`
   and `accept_workspace_invitation` both call a plugin callback
   (`validate_workspace_membership_mutation`) and the accept path fires
   `workspace_invitation_accepted` *before* deleting the invitation, so an
   additive listener can convert pending grants into real ones.

## Design

### Role and data model

A new workspace role string, `GUEST`, stored on the existing
`WorkspaceUser.permissions` / `WorkspaceInvitation.permissions` fields — no core
migration, exactly as `VIEWER` was done.

Two additive models under `backend/src/arabase/table_access/models.py`:

```
TableGrant
    workspace_user  FK WorkspaceUser (CASCADE)
    table           FK database.Table (CASCADE)
    level           CharField: VIEWER | EDITOR
    granted_by      FK User (SET_NULL)
    created_on / updated_on
    unique_together (workspace_user, table)

PendingTableGrant
    invitation      FK core.WorkspaceInvitation (CASCADE)
    table           FK database.Table (CASCADE)
    level           CharField: VIEWER | EDITOR
    unique_together (invitation, table)
```

`PendingTableGrant` exists only between invite and accept. The CASCADE matters:
core deletes the invitation right after acceptance, which cleans up the pending
rows once the listener has copied them.

A guest with zero `TableGrant` rows sees an empty workspace. That is the correct
failure mode — deny by default.

### Permission manager — deny by default

`TableGrantPermissionManagerType` in
`backend/src/arabase/permissions/table_grants.py`, registered in
`ArabaseConfig.ready()` and inserted into `settings.PERMISSION_MANAGERS`
immediately before `basic`, alongside `viewer_role`.

Its contract is the inverse of `viewer_role`: for a non-guest actor it returns
`{}` and every decision falls through to core unchanged; for a `GUEST` actor it
answers **every** check — allow only if the check passes the allowlist, deny
otherwise. A permission manager that only ever denies a fixed list of operations
is not safe here, because any operation added upstream later would silently
default to allowed.

Per check, for a guest:

1. Resolve `check.context` to its owning table with
   `object_scope_type_registry.get_by_model(context).get_parents(context)`,
   cached per request.
2. No table in the ancestry (the operation is workspace- or database-scoped) →
   allow only if the operation is in `WORKSPACE_LEVEL_ALLOWLIST` — `workspace.read`,
   `workspace.list_applications`, `application.read`, `database.list_tables` and
   the handful of read operations the app shell needs to boot — and, for a
   database-scoped context, only when that database holds at least one granted
   table. Everything else is denied.
3. Table in the ancestry → look up the `TableGrant`. Missing → deny. Present →
   allow if the operation is in the allowlist for that level.

Two allowlists, expressed as operation-type *names* (strings, not classes — the
same import-cycle avoidance `viewer_role.py` documents):

- **VIEWER**: `database.table.read`, `database.table.list_views`,
  `database.table.view.read`, `database.table.view.list_rows`,
  `database.table.view.read_row`, `database.table.view.list_fields`,
  `database.table.view.read_field_options`, `database.table.read_row`,
  `database.table.list_fields`, `database.table.view.list_filter`,
  `database.table.view.list_sort`, `database.table.view.list_group_bys`,
  `database.table.view.list_aggregations`, `database.table.view.read_aggregation`.
- **EDITOR**: VIEWER plus `database.table.create_row`,
  `database.table.update_row`, `database.table.delete_row`,
  `database.table.move_row`, `database.table.view.create_row`,
  `database.table.view.update_row`, `database.table.view.delete_row`,
  `database.table.read_row_history`.

Everything else is denied for guests by construction, which closes exports,
webhooks, snapshots, duplication, trash, API tokens, field and view mutation,
and every future operation, without enumerating them.

### Listing and filtering

`filter_queryset` on the same manager narrows:

- `workspace.list_applications` → databases that contain at least one granted
  table;
- `database.list_tables` → granted tables only.

That alone makes the sidebar show one database with one table.

### Invitation flow

No new email, token or accept page — core's are reused:

- **Create**: a new arabase endpoint `POST /api/arabase/table-access/invitations/`
  takes `{email, tables: [{table_id, level}], base_url}`. It calls
  `CoreHandler().create_workspace_invitation(..., permissions="GUEST")` and writes
  `PendingTableGrant` rows in the same transaction. Permission required:
  `CreateInvitationsWorkspaceOperationType` (workspace ADMIN), same as a normal
  invite.
- **Accept**: unchanged for the user — they click the emailed link and land on
  core's existing accept page. An arabase receiver on
  `workspace_invitation_accepted` copies `PendingTableGrant` → `TableGrant` for
  the new `WorkspaceUser`.
- **Manage**: arabase endpoints to list, re-level and revoke grants for a
  workspace, and to list pending invitations with their tables.

### Frontend

All additive, under `web-frontend/modules/arabase/`:

- A `GuestRoleType` registered into the existing `roles` registry
  (`web-frontend/modules/core/plugin.js:158,365-366`) plus role translations
  through a `PermissionManagerType`, exactly as
  `ViewerRoleTranslationsPermissionManagerType` does today
  (`web-frontend/modules/arabase/permissions.js`) — this is what makes the role
  render with a name instead of `undefined` in core's members table.
- A new workspace settings page registered on `workspaceSettingsPageTypes`:
  **وصول الجداول / Table access** — invite by email with a table picker and a
  level per table; list current guests and their tables; revoke.
- No sidebar work: the filtering is server-side, so a guest's sidebar is already
  correct.
- Arabic and English strings in both locale files, terms taken from
  `docs/GLOSSARY_AR.md` (add **ضيف** = guest, **وصول الجداول** = table access
  there first), CSS logical properties only.

## The hard part: linked fields

Hiding link-row, lookup and formula fields that read through to an ungranted
table is the one requirement the permission registry cannot satisfy, because
field listing is all-or-nothing on the table: `FieldsView.get`
(`backend/src/jadawel/contrib/database/api/fields/views.py:210-250`) checks
`ListFieldsOperationType` and then returns every field — it never calls
`filter_queryset`. Row payloads have the same shape: the serializer is built from
the table's model, so a link-row field carries the primary-field values of rows
in a table the guest was never granted.

This needs a bounded core patch, logged in `PATCHES.md`. The plan is to spike it
first (packet 5) rather than guess:

- **Preferred**: one `filter_queryset` call in `FieldsView.get`, plus a single
  choke point for row serialization. If the row serializer factory can take a
  `field_ids` allowlist that all read paths already funnel through, the patch is
  two files; if each read path builds its own serializer, the patch is wide and
  we fall back below.
- **Fallback for v1**: deny guests every path that emits row data other than
  grid/gallery row listing, and strip the offending fields in those two. Narrower
  product, far smaller blast radius.
- **Not chosen**: refusing to grant tables that have outbound links — it would
  reject most real tables.

Until the spike lands, treat linked-field hiding as unimplemented and do **not**
ship guest access for tables with outbound link, lookup or formula fields.

## Interactions and risks

- **Organization-managed workspaces reject this flow today.**
  `reject_legacy_workspace_membership_mutation`
  (`plugins/jadawel_organizations/backend/src/jadawel_organizations/handlers.py:27-44`)
  raises `PermissionDenied` for *any* core invitation into a workspace bound to an
  organization. v1 therefore covers unmanaged workspaces only; threading guests
  through the organizations plugin is a follow-up that also has to answer whether
  a guest consumes a Team seat. **This needs a product decision before v2.**
- **Realtime.** Row events go to a per-table websocket page whose subscription is
  permission-checked, so they are covered by the new manager. Workspace-level
  events sent with `broadcast_to_group` (`backend/src/jadawel/ws/tasks.py:276`)
  are not, so a guest could learn that *some* database was created. Metadata only,
  but worth an audit ticket.
- **Database tokens.** The `token` permission manager sits before ours in the
  chain; guests must not be able to create tokens (they cannot — token operations
  are outside the allowlist), but a token created by an admin still grants
  table-wide API access independently. No change needed, worth a test.
- **Trash and undo/redo** are outside the allowlist, so guests cannot restore or
  undo anything, including their own row edits. Acceptable for v1; call it out in
  the admin manual.
- **Search.** Workspace-wide search must not return rows from ungranted tables —
  needs an explicit test, since it may not route through `filter_queryset`.

## Work packets

Each packet is independently shippable and testable.

1. **Backend foundation** — `GUEST` role constant, the two models, migration
   (`arabase` app), and `makemigrations --check` clean.
2. **Permission manager** — deny-by-default checks, scope resolution with a
   per-request cache, `filter_queryset` for applications and tables,
   `get_permissions_object` returning granted table ids and levels. Registered
   in `ArabaseConfig.ready()` before `basic`.
3. **Invitation and grant API** — create/list/revoke endpoints under
   `/api/arabase/table-access/`, the `workspace_invitation_accepted` receiver,
   admin-only permission checks, OpenAPI annotations.
4. **Frontend** — `GuestRoleType`, role translations, the Table access settings
   page, `ar.json` + `en.json` parity, glossary entries.
5. **Linked-field spike** — enumerate every row-serialization path, decide
   between the two options above, write the patch and the `PATCHES.md` entry.
6. **Hardening** — search, realtime, tokens, trash and export tests; the
   organization-workspace interaction documented; admin manual updated.

## Testing

- Backend: `just b test -n=auto`, new tests under `backend/tests/arabase/` using
  the repo's DRF `APIClient` fixtures (`.agents/skills/write-backend-unit-test`).
  Minimum: a guest cannot list a non-granted table, cannot read its rows by id,
  cannot create a view, cannot export, sees exactly one application in
  `/api/applications/`; an Editor guest can write rows but not fields; revoking a
  grant takes effect immediately.
- Frontend: `just f test`, Vitest around the settings page and the role type.
- Fork hygiene: `pytest tests/arabase -q` and `yarn locale:check` are the two CI
  jobs easiest to miss locally (`AGENTS.md`).

## Out of scope for v1

Row-level and field-level permissions; restricting an existing member to a
subset of tables; grants at database scope; grants to groups rather than
individuals; guests in organization-managed workspaces; seat accounting for
guests; public share links (already exist and remain the answer for anonymous
read-only sharing).
