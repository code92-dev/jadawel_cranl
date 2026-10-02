# Baserow 2.4 feature port

Date: 2026-10-01. Source: Baserow `2.4.0` (`f8d94f48`), announced in the
[2.4 release notes](https://baserow.io/blog/baserow-2-4-release-notes).

Seven 2.4 features were brought into Jadawel. Everything else in 2.4 (Button
field, Graph element, Go to node, AI provider management, field permissions, the
dashboard grid, Airtable shared views, copying a view's configuration, rich form
descriptions, the builder changes, …) is out of scope and was not taken.

## Method

Jadawel's code is renamed (`baserow` → `jadawel`) and has diverged from upstream, so
`git merge` is not available (see `docs/RENAME_TO_JADAWEL.md`). Each feature was
taken from its upstream pull request as a three-way merge per file:

- base: the upstream file just before the pull request, renamed;
- theirs: the upstream file just after it, renamed;
- ours: the Jadawel file.

`git merge-file` then applies only that pull request's change. Conflicts were
resolved by hand, mostly where the change sat on top of an upstream 2.3 feature
Jadawel does not have. Upstream tests came along the same way and were trimmed where
they exercise such features. Every edit to an upstream-derived file is listed in
`PATCHES.md` under "Baserow 2.4 feature port".

Migrations were regenerated or renumbered onto Jadawel's own chain: database
`0214`–`0216`, automation `0030`–`0032`, integrations `0031`–`0032`, core
`0118`–`0120`.

## The features

| # | Feature | Upstream | Jadawel commit |
|---|---------|----------|----------------|
| 1 | Workspace homepage | #5977, #5980, #5992, #6001, #6002, #6107, #6108, #6176, #6205 | `feat(core): one homepage for every workspace and its items` |
| 2 | Images in rich text | #5775 (with prerequisite #5721) | `feat(database): images in rich text long text fields` |
| 3 | Start workflows from inbound email | #5730 | `feat(automation): start workflows from inbound email` |
| 4 | Return responses from workflows | #5595, #6168, #6182 | `feat(automation): return responses from workflows` |
| 5 | Stop a running workflow | #5924 | `feat(automation): stop a running workflow from its history` |
| 6 | Improved Group By views | #5787, #6022 | `feat(database): drag rows between groups and a Columns layout` |
| 7 | Data Sync history | #5706 | `feat(data-sync): keep and show the history of sync runs` |

### 1. Workspace homepage

After sign-in, `/dashboard` now redirects to `/all-workspaces`: every workspace in
one page, each as a box with its members, item count, role and its databases,
applications, dashboards and automations together as cards, sorted by when the user
last viewed them (or created, or by name), filterable by type and searchable
(`Ctrl K`). A dedicated sidebar lists the workspaces; `/recently-viewed` lists the
views, pages, dashboards and workflows the user opened, across workspaces.

The workspace page (`/workspace/<id>`) reads top to bottom as **Overview** (databases,
tables, rows, members), **Items** (everything in the workspace as the homepage's cards,
with the same type filter and sort), **Dashboard** (rows per database and rows added
over the last 30 days), then **Templates and API**. This differs from upstream, which
puts the resource links first and lists the recently viewed views and pages as "Your
items"; there, views named after their type read "Grid, Grid, Grid". Recently viewed
(`/recently-viewed`) keeps upstream's list, but titles a view with its table and shows
the view's own name underneath when it differs from its type.

Backend: `UserLastViewedItem` records what each user opens (views, builder pages,
dashboards, workflows), batched through a Celery singleton task;
`/api/last-viewed/items/` lists them; applications carry `last_viewed`; `UserProfile.preferences`
stores the sort and view mode; listing all applications filters permissions for all
workspaces in one pass (`CoreHandler.filter_queryset_for_workspaces`).

Adaptations:

- The workspace cookie that reopened the last workspace is gone, as upstream: a page
  selects a workspace only when its route names one.
- Jadawel has no workspace plan or row-usage badges (those come from Baserow's paid
  editions), so a workspace box shows members and items only.
- Builder pages are not trashable in Jadawel, so a deleted page's last-viewed rows are
  removed on `page_deleted`.
- `SkeletonBlock` and `usePageAsyncData` (from 2.4's skeleton loading) were added
  because the new components use them.
- The fork's featured-template cards on the workspace page were replaced by
  upstream's Templates card, which opens the same template picker.

### 2. Images in rich text

With "Enable rich text formatting" on, a long text cell takes images: uploaded from
the toolbar, dropped or pasted. They are stored as `![alt][user_file_name]`, served
with a signed URL that is stripped again on write, limited to 100 per cell, packed
into exports and counted in storage usage. The editor moved to TipTap's official
Markdown extension (#5721), which also fixes newlines disappearing. **Baserow 2.4 has
no tables in rich text**, so none were added.

TipTap is pinned to one release (3.27.4; core 3.30.5) as upstream does. Jadawel's
long text has no maximum length, so only the image limit is validated.

### 3. Inbound email trigger

"When an email arrives" gives a workflow its own address, `<token>@<domain>`
(`test-<token>@<domain>` runs the draft). A bundled [mox](https://www.xmox.nl/)
receiver accepts the mail and posts it to `/api/inbound-email/`; the backend deletes
each message from mox afterwards. The trigger is hidden, and refused by the API, until
`JADAWEL_INBOUND_EMAIL_DOMAIN`, `JADAWEL_INBOUND_EMAIL_WEBHOOK_SECRET` and the
receiver URL are set; see `docs/CONFIGURATION.md`.

**Deployment:** the backend image now builds mox, and the all-in-one image starts it
under supervisor when configured. CranL routes HTTP only, so on the current
deployment no mail server can reach it: the receiver has to run on a host with port 25
open, an MX record for the domain pointing at it, and
`JADAWEL_INBOUND_EMAIL_WEBHOOK_URL` pointing at the app.

The fork's step gallery shows the trigger in a new "Email" start category, and a
recipe "Save incoming emails as rows" is offered once the trigger is available.

### 4. Response step

A "Reply to the caller" step sets the status code, headers and body (empty, JSON or
text) of a run's answer. An HTTP trigger with "Wait for workflow response" holds the
request until the run reaches a Response step (or ends, answering `204`), up to its
timeout (bounded by `JADAWEL_AUTOMATION_WORKFLOW_RESPONSE_TIMEOUT_MAX_SECONDS`,
default 20). The answer is sent with `Content-Security-Policy: sandbox` and without
cookie, HSTS or CSP headers from the workflow. The `Caddyfile` replaced every app
route's policy with `frame-ancestors 'self'`, which would have dropped that `sandbox`
and let a reply's HTML run as the app's origin; `/api/webhooks/*` now gets
`sandbox; frame-ancestors 'self'` instead.

Not taken: the parts for 2.3's Start-workflow node and Manual trigger, which Jadawel
does not have. The status code field switches between a code picker and a formula in
the form itself, because Jadawel's formula input has no raw mode.

Note for this deployment: the wait occupies a web worker, and the single Celery worker
(concurrency 1) runs the workflow; if it is busy, the caller waits or gets `504`.

### 5. Stop a running workflow

A running entry in the workflow's history has "Cancel this workflow run". The run
stops before its next step (the current step finishes), shows as "Cancelled", and other
open editors update in real time. Only the cancel endpoint of upstream's
`api/history/` package was added, since the 2.3 node-history API is not in Jadawel.

### 6. Group By

Rows can be dragged within and between groups of a grouped grid view: the row takes
the target group's value and then moves, undone as one action. The view's group menu
switches between **Sections** (current) and **Columns** (group values in resizable
columns beside the rows, the pre-2.3 look). Column positions use logical insets so
they sit on the right in Arabic.

### 7. Data Sync history

Every sync is recorded as a job with who or what started it. "Update sync
configuration → Sync history" lists previous runs with start, duration, outcome and
error, and the sync modal attaches to a run still in progress.

## Verification

Backend: the touched apps' suites (automation, integrations core, database data
sync / views / rows / fields / import-export, core jobs / actions / last viewed /
users, applications, ws) and `tests/arabase`. Frontend: the core, database,
automation, integrations, dashboard and arabase unit suites; ESLint, Stylelint,
Prettier, Ruff and `yarn locale:check --strict`.

End to end, on a local instance running the branch's frontend and backend over the
production image: the homepage and workspace page in English and Arabic, recently
viewed, an image in a rich text cell, Group By in Columns layout in Arabic, the
"Answer a web request" recipe, and a published workflow answering a real request
with its Response step's status code, header and JSON body through Caddy.

Known pre-existing failures, unrelated to the port: the PostgreSQL data sync tests on
this host (the test database listens on port 55432, which overflows the `smallint`
port column), and `makemigrations --check` reporting a pending
`userprofile.language` alteration under the test settings.
