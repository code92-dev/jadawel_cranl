# 14: Assign members to managed workspaces

## What to build

Organization leaders create managed workspaces and grant members Admin, Member or Viewer workspace access.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Link a workspace to at most one organization; synchronize explicit access through core handlers and verified operation hooks.
- [ ] Organization leadership alone does not grant blanket data-reading authority.
- [ ] Provide workspace creation/access matrix and staff-only existing-workspace attachment preview, accounting for existing members and invitations.
- [ ] Reject unresolved outsiders rather than silently removing access; preserve unmanaged workspaces.
- [ ] Cover legacy member/invite endpoints and create/import/copy paths so they cannot bypass organization authority or seat limits; document minimal core hook patches if required.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 12: Invite and add organization members

