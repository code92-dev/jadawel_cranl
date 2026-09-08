# 19: Guide Team-to-Individual transitions

## What to build

An owner resolves organization workspaces and billing obligations before moving to Individual billing.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide a preview of workspaces, members, ownership, pending payments and effective timing.
- [ ] Require explicit resolution/transfer of managed workspaces and protect the sole owner; block unsupported destinations instead of auto-transferring data.
- [ ] Handle pending/unknown charges and scheduled renewal consistently; no duplicate personal account or unintended charge.
- [ ] Preserve organizational/financial history and unrelated memberships; no automatic deletion.
- [ ] Test interrupted/resumed transition and direct API attempts to bypass required resolutions.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 18: Apply billing restrictions to organization access

