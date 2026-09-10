# 09: Refund payments and record external payments

## What to build

A general administrator reviews refundable balances, issues a refund and records an external payment without corrupting Moyasar history.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide reason/amount/confirmation, persistent refund operation state, result/uncertain status and safe reconciliation.
- [ ] Verify provider refund idempotency support; otherwise reconcile an uncertain refund before retrying; prevent duplicate and excessive refunds.
- [ ] External payment records include reference/date/amount/reason and remain labelled external, not Moyasar revenue.
- [ ] Refunds and external records do not silently change independent manual grants; show access effects separately.
- [ ] Non-staff users cannot execute support mutations and all actions are audited.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 04: Recover uncertain payments from the admin panel

