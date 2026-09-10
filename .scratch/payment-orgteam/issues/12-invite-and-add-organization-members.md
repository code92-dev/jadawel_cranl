# 12: Invite and add organization members

## What to build

Owners/administrators invite employees and the general administrator can add existing users, with seat-safe acceptance.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide people/invite lists, role selection, invite/resend/cancel, direct staff addition and acceptance UI using existing identity/email infrastructure.
- [ ] Hash invitation tokens, normalize email, enforce matching verified email, expiry and replay protection; send mail after commit.
- [ ] Pending invitations do not consume seats; owner does; serialize acceptance and direct additions against manual/purchased capacity.
- [ ] Concurrent last-seat acceptance admits only one member; expired/mismatched/replayed invitations fail clearly.
- [ ] Prevent duplicate usable invites and cross-organization access; ordinary admins cannot assign Owner/Admin authority.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 11: Create a complimentary organization

