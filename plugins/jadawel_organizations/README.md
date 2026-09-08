# Jadawel Organizations plugin

Tested against Jadawel revision `a7d171a`.

This standalone plugin adds Team organization accounts on top of the separate
`jadawel_billing` plugin. It provides general-administrator free provisioning,
owners, administrators, members, invitations, workspace bindings and lifecycle
controls. Payment is never performed by this package.

Install billing first, then install this backend package and include the frontend
module in `ADDITIONAL_MODULES`:

```bash
uv pip install ./plugins/jadawel_billing/backend ./plugins/jadawel_organizations/backend
export JADAWEL_PLUGIN_DIR="$PWD/plugins"
export ADDITIONAL_MODULES="../plugins/jadawel_billing/web-frontend/modules/jadawel-billing/module.js,../plugins/jadawel_organizations/web-frontend/modules/jadawel-organizations/module.js"
```

Run `jadawel migrate` after installation. Existing workspaces are unchanged until
an administrator explicitly binds one to an organization. Organization data is
retained when the plugin is removed; take a database backup before schema changes.

The namespaced API is mounted under `/api/organizations/`. It includes member
list/add/update/remove, invitation create/list/accept/revoke, restricted owner
setup invitations with resend/reassign controls, workspace outsider previews,
bind/unbind and member assignment, lifecycle controls, audit history, and the
Team-to-Individual transition. Owners and organization admins are separate from
Django staff users; the general administrator uses `is_staff` for complimentary
provisioning, lifecycle recovery, and outsider resolution.

Team membership is capacity-locked against the Billing entitlement. Active and
suspended memberships both reserve seats; ordinary pending invitations do not,
while a pending owner setup invitation reserves the owner seat. Removing a
member releases their seat, while suspending them removes managed workspace
access and preserves the reservation.
