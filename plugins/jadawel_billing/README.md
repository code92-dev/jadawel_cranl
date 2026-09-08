# Jadawel Billing plugin

This standalone plugin provides the billing account, plan and price catalogue,
administrator-managed complimentary entitlements, and the first Moyasar payment
verification path for Jadawel. It supports individual accounts today; Team
checkout remains disabled until the Organizations plugin provisions a Team
account and its members.

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
plans, prices, grants, suspensions and audit history. An account payer can create
an individual order and request verification. Moyasar events are accepted at
`/api/billing/moyasar/webhook/`, stored idempotently, and reconciled by the
`jadawel_billing.reconcile_payments` Celery task.

Complimentary access is an explicit, audited grant with a plan, seat cap, start,
optional expiry, reason and revision. Editing or revoking a grant does not
create a payment or silently cancel a paid renewal.

## Removal and upgrades

Upgrade by running normal migrations before restarting workers and the frontend.
Removing the package does not delete billing records. Disable customer billing
traffic and preserve the database and payment evidence before uninstalling the
plugin from a deployment.

Focused backend checks are run with:

```bash
DATABASE_HOST=127.0.0.1 \
PYTHONPATH=backend/src:backend/tests:plugins/jadawel_billing/backend/src \
JADAWEL_PLUGIN_DIR="$PWD/plugins" \
backend/.venv/bin/python -m pytest -c backend/pytest.ini \
plugins/jadawel_billing/tests -q --reuse-db
```
