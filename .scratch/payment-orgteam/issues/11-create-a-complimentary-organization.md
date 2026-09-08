# 11: Create a complimentary organization

## What to build

A general administrator creates a free Team organization with an owner and seat allowance from a working creation wizard.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Install separate Organizations plugin requiring Billing; fail clearly if missing, while Billing continues to load alone.
- [ ] Atomically create Team account/manual grant/organization with unique linkage and idempotent creation; no credentials, payment or provider calls.
- [ ] Support an existing owner or pending owner setup invitation with reserved owner seat; resend/reassign pending ownership safely.
- [ ] Show organization overview/settings and audit; preserve one active owner once activated.
- [ ] Do not automatically attach existing workspaces or paywall existing users.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 10: Verify Billing installation and administrator workflows

