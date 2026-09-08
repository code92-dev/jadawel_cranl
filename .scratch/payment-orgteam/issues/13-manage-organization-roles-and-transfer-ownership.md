# 13: Manage organization roles and transfer ownership

## What to build

An owner appoints administrators or transfers ownership to an active member through an audited review flow.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Enforce Owner/Admin/Member hierarchy consistently in API and UI; no self-promotion or staff flag changes.
- [ ] Protect exactly one owner under concurrent transfers, demotion and deletion attempts.
- [ ] Show successor and explicit payer-responsibility review; changing organization owner never silently changes payer or data access.
- [ ] Provide paginated/searchable role views and audit actor/before/after; test unrelated organizations.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 12: Invite and add organization members

