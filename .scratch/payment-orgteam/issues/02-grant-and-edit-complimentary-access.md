# 02: Grant and edit complimentary access

## What to build

A general administrator assigns, edits, extends and revokes manual Individual or Team access while seeing the effective access and its audit history.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide plan/capacity/start/optional expiry/reason forms with a before/after preview; manual grants never fabricate paid transactions.
- [ ] Enforce suspension > valid manual grant > paid/grace > restricted precedence; grant replacement, expiration and paid fallback are deterministic and cache-safe.
- [ ] Serialize grant/capacity edits, protect audit history and keep provider payment facts independent.
- [ ] Display paid renewal status and never silently cancel renewals or trigger charges when a grant changes.
- [ ] Prove denied non-staff access, expiry boundaries, audit before/after and zero provider calls.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 01: Manage billing accounts and versioned plans

