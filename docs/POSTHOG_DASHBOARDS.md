# Jadawl PostHog setup and dashboard definitions

Status (7 September 2026): PostHog EU project `260085` is named **Jadawl**,
has `https://app.jadawl.site` as its app URL, and reports in `Asia/Riyadh`.
Production browser and backend ingestion are verified. Nine private, pinned
Jadawl dashboards contain 27 saved insights. The six additional dashboards and
the modified original product charts were executed after their final changes.

The owner approved using the existing instrumentation in PostHog EU, including
user emails, page URLs, and action metadata. IP anonymization remains enabled;
session recording remains disabled.

## Production configuration

Set `POSTHOG_PROJECT_API_KEY` to the project's ingestion key from PostHog settings
and `POSTHOG_HOST` to `https://eu.i.posthog.com`.
Do not use an OAuth token or personal API key as the ingestion key.
These existing variables feed both Django and Nuxt through `env-remap.mjs`.
Save the deployment environment and reload through CranL's documented workflow.
These settings were saved on CranL app `jadawel-org`
(`8ff2d656-4fde-4513-adf3-6b9c20434867`) and Actions → Reload completed.
The public root, login and `/api/_health/` returned HTTP 200. Root and login HTML
exposed the configured EU host and no empty PostHog key. Browser `$pageview` and
backend `update_rows`, `create_view`, and `update_view` were observed in PostHog.
No code deployment or synthetic product action was needed for verification.

## Created dashboards

- [Traffic overview](https://eu.posthog.com/project/260085/dashboard/937226):
  period visitors, pageviews, daily visitors, visited paths and referring domains.
- [Tracking health & audience](https://eu.posthog.com/project/260085/dashboard/937227):
  ingestion freshness, observed event coverage, device and browser breakdowns.
- [Editing & workspaces](https://eu.posthog.com/project/260085/dashboard/937230):
  unique row editors, bulk update operations, daily editors and editing workspaces.

Native trend charts default to 28 days and respect dashboard date controls.
The diagnostic SQL windows are explicitly fixed: 24 hours for coverage and a
seven-day lookup for freshness. Missing freshness is null, not zero.
Browser charts filter `$host = app.jadawl.site`; backend charts have no browser
hostname requirement. The editing dashboard currently covers observed
`update_rows` only. Bulk actions count operations, not rows changed.

At verification: two pageviews from one person, six bulk row-update operations
from one person in one workspace. These are setup-period observations, not a
customer-adoption baseline. Tracking began 6 September 2026; earlier zeros mean
no collected history. A 1–5 September override correctly returned zero editing
activity without changing saved defaults. Traffic dashboard rendering was also
checked in the authenticated PostHog browser.

Product charts now exclude the owner-specified test email and the existing
internal domain `@code92.dev`, matching event `user_email` with person
`user_email` as fallback. The exact owner-supplied address is stored only in
PostHog chart definitions, not this repository. Validation confirmed all six
observed row updates were excluded. Unknown/anonymous accounts can still appear.
Performance and tracking-health dashboards intentionally include internal traffic.
Existing cohort `223806` checks a different `email` property. It was not modified;
MCP lacks cohort write access. Explicit chart filters avoid relying on that cohort.
The metric catalog is empty, so these are project-specific metric definitions.

## Additional dashboards (7 September 2026)

- [Performance & errors](https://eu.posthog.com/project/260085/dashboard/937243):
  FCP daily p75, FCP and LCP by page with sample counts, and live browser capture
  configuration confirmation. Performance SQL uses seven days; confirmation
  uses 24 hours. Missing days are not plotted as zero performance.
- [Feature adoption](https://eu.posthog.com/project/260085/dashboard/937248):
  unique users and daily operations for observed row updates and view actions.
- [Workspace engagement](https://eu.posthog.com/project/260085/dashboard/937249):
  daily editing workspaces and a fixed 28-day editor/activity table.
- [Retention & habits](https://eu.posthog.com/project/260085/dashboard/937250):
  recurring weekly editor cohorts and fixed 28-day editing-day distribution.
- [Onboarding & activation](https://eu.posthog.com/project/260085/dashboard/937251):
  first observed editors and ordered visit-to-edit within seven days. This is
  not signup conversion or proof of same-workspace activation.
- [Collaboration](https://eu.posthog.com/project/260085/dashboard/937252):
  contributors per workspace and workspaces with two or more editors (28 days).

Project settings `autocapture_exceptions_opt_in` and
`autocapture_web_vitals_opt_in` were enabled remotely. The installed posthog-js
SDK honors these settings without a code deployment. Received live telemetry
confirmed both settings true, and FCP/LCP measurements arrived through normal
browser use. Session recording remains disabled. No artificial exceptions,
invitations, signups, or production data changes were created for analytics.

Limits: INP/CLS samples and actual exception delivery remain unverified. Browser
capture covers unhandled errors/rejections; caught Vue errors and Django failures
need separate instrumentation. The error panel links to native Error tracking;
the dashboard widget feature is not enabled. Signup and invitation conversion
remain pending event coverage; retention needs mature follow-up periods. All
limits are stated on the dashboards. No full signup/acceptance funnel is claimed.

## Future definitions requiring additional event coverage

### Product overview

- Weekly active editors: distinct identified users performing `create_row`,
  `create_rows`, `update_row`, or `update_rows` in the selected seven-day window.
  This measures editing, not passive viewing.
- Active workspaces: distinct non-null `workspace_id` values on those events.
- Daily editor trend over 28 days, with previous-period comparison.
- Feature adoption: distinct users creating tables, importing rows, installing
  templates, exporting applications, and inviting collaborators.
- Tracking health: latest browser event and latest backend action timestamps.

### Activation and collaboration

- First-value funnel: `create_application` (database type), `create_table`, then
  first row creation within seven days. This is a user-level funnel; it does not
  prove all steps occurred in the same workspace. Label this limitation.
- Template-led activation is a separate path, because template installation can
  bypass manual database and table creation.
- Invitation volume and acceptance volume are separate trends. Do not divide
  inviter and invitee unique-user counts to claim an invitation conversion rate.
- Verify account signup instrumentation before adding signup conversion.

### Retention

- Weekly editor retention: users who edit in the starting week and edit again in
  subsequent weeks, over eight weeks. Treat incomplete weeks as immature cohorts.
- Active editing days per user over 28 days, rather than raw event volume.
- Distinguish new, returning, resurrected, and dormant editors only when sufficient
  observation history exists.

## Validation gates

Verify event names, properties, and values in PostHog's live schema before creating
queries. Names above come from repository action classes and are not yet verified
as ingested unless explicitly listed in the verified scope above. Bulk actions
represent operations, not necessarily numbers of rows.
Use observed production properties for filtering; backend events do not currently
include a browser hostname. Inspect the existing test-account cohort/filter before
enabling it globally. No arbitrary targets, synthetic user events, fabricated
history, or revenue metrics should be added.

Required discovery permissions include `action:read`, `data_catalog:read`, and
`cohort:read`, in addition to project, event/property definitions, query, dashboard,
and insight permissions. Keep dashboard sharing private to the existing project.
