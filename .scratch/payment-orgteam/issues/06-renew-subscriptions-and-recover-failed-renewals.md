# 06: Renew subscriptions and recover failed renewals

## What to build

Consenting customers renew automatically and can recover from a failed or challenge-required renewal through billing screens.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Use durable schedule/attempt state, one current subscription, period locks and one charge identity per logical renewal; no DB transaction spans provider HTTP.
- [ ] Implement configurable grace and bounded retries; proposed 7-day grace and day-1/day-3 retries remain unconfirmed launch policies.
- [ ] Unknown results reconcile before another charge; challenges request customer action; successful recovery restores effective paid entitlement.
- [ ] Test duplicate workers, restart after charge, revoked token, missing event, month-end/leap-year timing and expired/manual-only grants.
- [ ] Expose renewal date, status, recovery action and safe administrator diagnostics.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 04: Recover uncertain payments from the admin panel
- Draft 05: Manage saved payment methods and recurring consent

