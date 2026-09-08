# 16: Suspend, reactivate and archive organizations

## What to build

A general administrator suspends or restores an organization and its public access; an owner can archive it with retained data.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Show impact/retention and separate renewal control; organization suspension overrides paid/manual access without fabricating payment state.
- [ ] Disable public sharing during organization suspension while preserving configuration; restore only according to saved policy.
- [ ] Preserve workspaces/audit/payment history; no permanent deletion in v1.
- [ ] Prevent legacy APIs, tokens and background actors from bypassing organization lifecycle restrictions.
- [ ] Organization management authority remains distinct from blanket workspace data-reading access.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 15: Suspend or remove members and revoke their access

