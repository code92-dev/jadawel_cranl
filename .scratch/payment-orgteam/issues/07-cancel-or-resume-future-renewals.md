# 07: Cancel or resume future renewals

## What to build

A payer or audited general administrator stops future renewals while preserving the paid period, and can resume with explicit consent.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide cancellation/resumption review with effective date; no automatic refund or data deletion.
- [ ] Serialize cancellation against due/in-flight renewal and show any unresolved charge rather than promising a cancellation already too late.
- [ ] Manual grants do not cancel paid renewals; the grant screen links to this explicit action.
- [ ] Test period boundaries, cancellation races and no unauthorized payer changes.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 06: Renew subscriptions and recover failed renewals

