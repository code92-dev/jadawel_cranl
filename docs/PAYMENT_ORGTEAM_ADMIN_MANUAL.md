# Jadawel billing administrator manual

This guide describes the billing and complimentary-access controls delivered by
the `jadawel_billing` plugin. It is written for a Jadawel general administrator
(`is_staff`). Payment state and effective access are separate: a paid order is
activated only after the server verifies it with Moyasar, while a complimentary
grant is an audited entitlement change and never a payment.

## Configure and install

Install the plugin package and enable it through the normal Jadawel plugin
loader. Configure these values outside the admin UI:

- `JADAWEL_MOYASAR_SECRET_KEY` and `JADAWEL_MOYASAR_PUBLISHABLE_KEY` use the
  same `test` or `live` prefix as `JADAWEL_BILLING_MODE`.
- `JADAWEL_MOYASAR_WEBHOOK_SECRET` authenticates the Moyasar webhook.
- `JADAWEL_BILLING_LIVE_ENABLED` must be explicitly enabled before live mode
  can be selected.

The plugin works without Moyasar keys for administrator-created complimentary
access. Do not place card numbers, CVC values, or secret keys in Jadawel
requests, logs, or screenshots. Card details go directly from the browser to
Moyasar.

## Create an account without payment

1. Open **Billing** in the administrator area and choose **Create account**.
2. Enter the active responsible user's email and choose **Individual** or
   **Team**. Account creation is audited and does not contact Moyasar.
3. Select **Complimentary access** for the account, choose a plan, set the seat
   limit and optional expiry, and enter a support reason.
4. Choose **Review access change**. Confirm the plan, seats, start/expiry and
   current paid renewal shown by the panel, then choose **Confirm**.

The account's effective source becomes **Complimentary** when the grant is
within its start and expiry window. A general administrator can use this flow
with Moyasar configuration absent.

## Edit, extend, or revoke access

Open the account's **Complimentary access** panel. Change the plan, seat limit,
expiry, or reason and review the complete proposed state before saving. A seat
limit below current usage is rejected while holding the account capacity lock;
resolve membership usage first rather than removing users implicitly.

To extend access, set a later expiry and save a new reason. To end it, choose
**Revoke grant**, enter a reason, and confirm. Revocation falls back to a valid
paid subscription or **Restricted** access. It does not cancel a paid renewal,
issue a refund, or delete data. Every change appears in **Activity history**
with before/after details.

**Suspend account access** takes precedence over both complimentary and paid
entitlements. **Restore account access** removes that administrative
suspension; it does not create a subscription.

## Verify and reconcile payments

The customer billing page creates an immutable order quote and submits the card
directly to Moyasar. The customer can return to **Verify payment** after a
redirect, timeout, or abandoned callback. A provider payment ID is reused for
the same order until its state is resolved; a failed payment can be retried
with a new order attempt after the failed order is visible.

In the administrator **Payments** list:

1. Confirm the account, amount, currency, mode, provider reference and attempt
   status.
2. For a pending order, choose **Verify with Moyasar**. This performs a fresh
   server-side fetch and checks the provider ID, amount, currency, order
   metadata and settled `paid` status.
3. Use **Provider events** to inspect webhook event IDs, processing state,
   attempt count and retry error. Events are idempotent, retained when a
   callback arrives late, and reclaimed after a worker lease expires.

Paid orders show a **Payment receipt** with the Moyasar reference, paid time,
amount/currency and the subscription access period. A receipt is evidence of a
verified payment; do not label it a tax invoice without an approved invoicing
solution.

## Operational boundaries

The current plugin slice covers personal checkout, plan and price catalogue
management, manual entitlements, reconciliation, audit history and receipts.
Saved payment tokens, recurring renewals, refunds, and the separate
organization/membership plugin remain planned tickets (#46–#61). Do not create
an organization by editing billing rows directly; use the organization plugin
provisioning workflow once that package is implemented.
