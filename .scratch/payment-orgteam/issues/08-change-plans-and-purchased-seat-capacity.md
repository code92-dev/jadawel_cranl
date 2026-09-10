# 08: Change plans and purchased seat capacity

## What to build

A payer previews and pays for increased capacity or schedules an eligible plan/seat reduction.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Calculate prorated increases server-side with documented UTC period math, rounding and immutable quote snapshots; capacity changes only after verified payment.
- [ ] Schedule reductions for renewal; use the capacity contract and reject below active-plus-suspended usage with a clear resolution message.
- [ ] Show current and pending price/seat state and preserve receipt history when catalogue prices change.
- [ ] Use a contract test capacity provider before Organizations exists; prevent self-service Team sales without its capability.
- [ ] Leave organization-to-personal migration gated until the dedicated transition slice is complete.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 07: Cancel or resume future renewals

