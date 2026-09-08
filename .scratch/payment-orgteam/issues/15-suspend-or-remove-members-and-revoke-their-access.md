# 15: Suspend or remove members and revoke their access

## What to build

A leader suspends, reactivates or removes a member and sees managed access revoked immediately while data is retained.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide impact preview and audited lifecycle actions; protect owner and reject unauthorized peer/admin mutations.
- [ ] Suspension retains a seat; removal releases it; reactivation rechecks entitlement and access policy.
- [ ] Enforce revocation for existing API credentials, cached permissions, websocket updates and user-delegated automation/integration actors.
- [ ] Test direct/legacy API bypass, live-session revocation and multiple organizations/personal workspaces remaining independent.
- [ ] Document that intentionally public data remains public on member removal; retain history and never delete the global user account.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 13: Manage organization roles and transfer ownership
- Draft 14: Assign members to managed workspaces

