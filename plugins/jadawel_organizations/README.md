# Jadawel Organizations plugin

This standalone plugin adds Team organization accounts on top of the separate
`jadawel_billing` plugin. It provides general-administrator free provisioning,
owners, administrators, members, invitations, workspace bindings and lifecycle
controls. Payment is never performed by this package.

Install billing first, then install this backend package and include the frontend
module in `ADDITIONAL_MODULES`:

```bash
uv pip install ./plugins/jadawel_billing/backend ./plugins/jadawel_organizations/backend
export JADAWEL_PLUGIN_DIR="$PWD/plugins"
export ADDITIONAL_MODULES="$PWD/plugins/jadawel_billing/web-frontend/modules/jadawel-billing/module.js,$PWD/plugins/jadawel_organizations/web-frontend/modules/jadawel-organizations/module.js"
```

Run `jadawel migrate` after installation. Existing workspaces are unchanged until
an administrator explicitly binds one to an organization. Organization data is
retained when the plugin is removed; take a database backup before schema changes.

For a source checkout, build the frontend with both modules in dependency order:

```bash
export ADDITIONAL_MODULES="$PWD/plugins/jadawel_billing/web-frontend/modules/jadawel-billing/module.js,$PWD/plugins/jadawel_organizations/web-frontend/modules/jadawel-organizations/module.js"
yarn --cwd web-frontend build
```

Upgrade by installing matching Billing and Organizations revisions, running all
migrations, and restarting workers and the frontend. To remove the plugin,
disable organization traffic first, preserve managed workspace data and audit
records, back up the database, and remove Organizations before Billing. The
packages never delete organization, billing, or workspace records during
removal.

The namespaced API is mounted under `/api/organizations/`. It includes member
list/add/update/remove, invitation create/list/accept/revoke, restricted owner
setup invitations with resend/reassign controls, workspace outsider previews,
bind/unbind and member assignment (ADMIN, MEMBER, or read-only VIEWER), lifecycle
controls, audit history, and the Team-to-Individual transition. A general
administrator must explicitly confirm a binding preview when existing outsiders
are present. Owners and organization admins are separate from
Django staff users; the general administrator uses `is_staff` for complimentary
provisioning, lifecycle recovery, and outsider resolution.

Organization, member, invitation, workspace, audit, and administrator lists use
the standard `{count, next, previous, results}` pagination envelope. Pass a
`search` query parameter to filter organization names/owners, member identities,
invitation addresses, workspace names, or audit action/target values.

Team membership is capacity-locked against the Billing entitlement. Active and
suspended memberships both reserve seats; ordinary pending invitations do not,
while a pending owner setup invitation reserves the owner seat. Removing a
member releases their seat, while suspending them removes managed workspace
access and preserves the reservation.

Backend tests are not run by CI. The Billing and Organizations suites import
each other, so run them together from `backend/`, with the same `DATABASE_*`
settings as the core suite. `JADAWEL_PLUGIN_DIR` must be exported before pytest
starts, because the settings read it at import time to load both plugins:

```bash
export JADAWEL_PLUGIN_DIR="$PWD/../plugins"
export PYTHONPATH="tests:src:$JADAWEL_PLUGIN_DIR/jadawel_billing/backend/src:$JADAWEL_PLUGIN_DIR/jadawel_organizations/backend/src"
.venv/bin/pytest -c pytest.ini ../plugins/jadawel_billing/tests ../plugins/jadawel_organizations/tests
```
