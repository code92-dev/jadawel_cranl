# 04: Recover uncertain payments from the admin panel

## What to build

Customers see pending payment recovery and administrators reconcile delayed or uncertain Moyasar results without charging twice.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Durably record sanitized authenticated events before acknowledgement, retry processing and expose status/retry results in the admin panel.
- [ ] Retain original payment identity during timeout/restart recovery; do not issue a fresh charge while the prior outcome is unknown.
- [ ] Prevent stale/out-of-order events from regressing state and never overwrite manual grants.
- [ ] Test missing/duplicate webhook, callback race, provider success followed by database failure, wrong environment and recovery after restart.
- [ ] Record sandbox success/failure verification and current provider sources; missing credentials are an explicit evidence blocker, not a passing check.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 03: Buy an Individual subscription with Moyasar

