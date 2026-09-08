# Moyasar billing and organization implementation progress

Branch: `payment-Orgteam-plugins`. Executor: current Codex task. Review base:
`a7d171a12de08174999adcf43f620b14569c08c0`. No deployment or live charge was
performed.

## Implemented slices

The two standalone packages are now present in the working tree:

- `plugins/jadawel_billing`: Individual and Team accounts, immutable plans and
  price versions, complimentary grants, Moyasar quote/verification and webhook
  reconciliation, receipts, saved payment methods, renewal state and grace
  handling, scheduled subscription changes, prorated Team seat increases,
  refunds, external payment records, and general-admin refund/payment controls.
- `plugins/jadawel_organizations`: Team organization provisioning, owner/admin/
  member roles, existing-user adds, hashed invitations and acceptance, revoke
  and resend behavior, seat locking, workspace binding and member assignment,
  organization permission enforcement, suspend/reactivate/archive, paid-Team
  provisioning, guided Team-to-Individual transition, and the general-admin
  pending-owner setup invitation with reserved owner capacity.

The corresponding GitHub ticket frontier is #42–#61. The branch contains the
implementation for the billing and organization management paths in those
slices; the issues remain open until a maintainer reviews and lands the branch.

## Verification completed

Focused backend verification, with both plugin paths loaded, currently passes:

```text
64 passed
```

The same run covers complimentary access, role authority, seat reservation for
suspended members, invitation mismatch/expiry/replay, workspace revocation and
restoration, preservation of pre-existing workspace access, restricted operation
handling, paid-Team idempotent provisioning, per-seat Team quotes, payment
verification, webhook reconciliation, active Moyasar token/payment binding,
payment methods, refunds, and renewal task behavior. The focused frontend run
passes 9 tests, and strict repository locale parity reports 3,787/3,787 keys.

The organization UI now previews workspace outsiders before binding, supports
pending-owner reassignment, and exposes the guarded Team-to-Individual
transition. Billing administration lists external payments and supports
provider refunds with a refundable-balance confirmation. Organization settings
can be renamed with an audit record; bindings require explicit outsider
confirmation for general administrators and support ADMIN, MEMBER, and
read-only VIEWER assignments, including per-member unassignment without
removing the organization membership.

Additional checks completed during implementation include scoped Ruff checks,
Django system checks, Nuxt `prepare`, standalone locale parity, and Prettier
checks for changed frontend files.
Provider HTTP calls for saved payment methods are outside the database write
transaction.

The organization tests also cover pending-owner acceptance, reserved owner
capacity, restricted workspace creation, and the public-workspace policy.

## Local run

The local services used for verification are:

- Frontend: [http://localhost:3003/billing](http://localhost:3003/billing)
- Organization member panel: [http://localhost:3003/organizations](http://localhost:3003/organizations)
- General-admin organization panel: [http://localhost:3003/admin/organizations](http://localhost:3003/admin/organizations)
- Backend: `http://localhost:8003`

Use `localhost` for the browser host. Jadawl's public-host routing intentionally
treats `127.0.0.1` as a public-page host and returns the public-page 404 for
authenticated routes.

The local process is configured with both plugin modules and no live Moyasar
credentials. Administrator-created complimentary organizations work without
provider keys. A real sandbox payment, 3-D Secure flow, and production build
still require valid test credentials and a browser-authenticated fixture. The
manual currently documents the flows; actual screenshot capture remains a V01
release gate.

## Remaining release gates

Before enabling production billing, obtain and verify the merchant's actual
prices, tax/invoice treatment, refund policy, recurring-payment eligibility,
grace policy, and Moyasar webhook configuration. Run the disposable-image fresh
install/upgrade checks and a browser-authenticated Arabic/English pass with
Moyasar sandbox credentials. The organization adapter still needs a dedicated
integration pass for public-share, websocket, delegated-job and legacy import
surfaces before those paths are described as fully managed. Do not mark these
provider- or integration-dependent checks as passed from the local no-key run.
