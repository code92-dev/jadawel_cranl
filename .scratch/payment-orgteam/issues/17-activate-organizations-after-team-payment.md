# 17: Activate organizations after Team payment

## What to build

A Team buyer completes checkout and receives exactly one organization, with a recoverable provisioning screen if setup fails.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Register Team availability only when Organizations and durable provisioning are healthy.
- [ ] Verified payment queues durable idempotent provisioning; crash/retry cannot lose a paid purchase or duplicate an organization.
- [ ] Show pending/retry/ready states, owner setup and purchased capacity in billing and organization views.
- [ ] Transition complimentary accounts to paid only with payer consent and a verified order; preserve manual grant precedence.
- [ ] Exercise paid-success/provisioning-failure/restart paths in sandbox and prevent user-controlled payment reassignment.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 11: Create a complimentary organization
