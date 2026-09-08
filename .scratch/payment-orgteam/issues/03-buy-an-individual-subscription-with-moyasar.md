# 03: Buy an Individual subscription with Moyasar

## What to build

A customer chooses an Individual plan, completes sandbox checkout and sees server-verified subscription activation and a receipt.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Implement server-owned immutable quote/order, browser Moyasar form, callback/result screen, persistent payment attempt and initial subscription period.
- [ ] Card data goes directly to Moyasar; secret keys/tokens stay server-side; test/live are isolated and live charging defaults off.
- [ ] Verify official webhook authentication/envelope and provider statuses; authenticate notification and fetch payment server-side before activation.
- [ ] Match amount, currency, environment and order; reject reused payments, forged callbacks and initiated/authorized-only results.
- [ ] Persist a stable given_id across uncertain retries; duplicate callbacks/events cannot double-activate. Show failed/abandoned/3DS outcomes.
- [ ] Account-scoped history/receipts are accessible only to authorized users. Hide Team checkout until Organizations is installed and provisioning-ready.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 02: Grant and edit complimentary access

