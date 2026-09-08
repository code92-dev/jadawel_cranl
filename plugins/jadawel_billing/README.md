# Jadawel Billing plugin

Tested against the `payment-Orgteam-plugins` branch at commit `9dd6623`.
The branch's documented core hooks in `PATCHES.md` are required for managed
workspace membership enforcement; do not install this package against an older
Jadawel revision without those hooks.

This standalone plugin provides the billing account, plan and price catalogue,
administrator-managed complimentary entitlements, and Moyasar payment
verification for Jadawel. It supports Individual accounts on its own. When the
separate Organizations plugin is installed, it also quotes and activates Team
subscriptions and provisions the organization through the registered Team
provisioner.

## Installation

Install the backend package from this plugin directory and install the frontend
module with the same plugin release. The Jadawel plugin loader discovers the
folder when it is included in `JADAWEL_PLUGIN_DIR`:

```bash
uv pip install ./plugins/jadawel_billing/backend
```

Run the plugin migrations with the normal Jadawel migration command. The
frontend module is loaded by the standalone plugin installer; it depends on the
core Nuxt module and registers `/billing` and `/admin/billing`.

For a source checkout, include the module in the Nuxt build and restart the
frontend after dependencies are installed:

```bash
export ADDITIONAL_MODULES="$PWD/plugins/jadawel_billing/web-frontend/modules/jadawel-billing/module.js"
yarn --cwd web-frontend build
```

## Configuration

Set these values outside the repository when enabling Moyasar:

| Setting | Purpose |
| --- | --- |
| `JADAWEL_MOYASAR_SECRET_KEY` | Server-only key used to verify payments |
| `JADAWEL_MOYASAR_PUBLISHABLE_KEY` | Browser key used for card entry |
| `JADAWEL_MOYASAR_WEBHOOK_SECRET` | Shared secret for the webhook endpoint |
| `JADAWEL_BILLING_MODE` | `test` (default) or `live` |
| `JADAWEL_BILLING_LIVE_ENABLED` | Explicit `true` gate before live mode is accepted |

Absent Moyasar settings do not prevent administrator-created complimentary
access. The server calculates every order amount and verifies the provider
payment, amount, currency, environment and order metadata before activating a
subscription. Card details are submitted directly from the browser to Moyasar;
they are never sent to the Jadawel API.

## API and operations

The namespaced API is mounted under `/api/billing/`. Staff users manage accounts,
plans, prices, grants, suspensions, subscriptions, refunds and audit history.
An account payer can create an Individual or (when Organizations is installed)
Team order and request verification. Moyasar events are accepted at
`/api/billing/moyasar/webhook/`, stored idempotently, and reconciled by the
`jadawel_billing.reconcile_payments` Celery task.

Complimentary access is an explicit, audited grant with a plan, seat cap, start,
optional expiry, reason and revision. Editing or revoking a grant does not
create a payment or silently cancel a paid renewal.

Reusable payment methods are saved only after a paid payment is verified against
the same billing account and Moyasar reports the token as `active`. Revoking a
method prevents future renewals from using it; the provider token itself is
never exposed in API responses.

## Removal and upgrades

Upgrade by installing the matching backend/frontend revision, running normal
migrations before restarting workers and the frontend, and keeping Billing
installed before any Organizations upgrade. Removing the package does not
delete billing records. Disable customer billing traffic, preserve the database
and payment evidence, and complete a backup before uninstalling the plugin from
a deployment.

Focused backend checks are run with:

```bash
DATABASE_HOST=127.0.0.1 \
PYTHONPATH=backend/src:backend/tests:plugins/jadawel_billing/backend/src \
JADAWEL_PLUGIN_DIR="$PWD/plugins" \
backend/.venv/bin/python -m pytest -c backend/pytest.ini \
plugins/jadawel_billing/tests -q --reuse-db
```
