# 01: Manage billing accounts and versioned plans

## What to build

A general administrator installs Billing alone, creates Individual or Team billing accounts, and manages a versioned plan catalogue through the admin panel.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Verify current extension, permission, task-discovery and test hooks; document exact integration contracts and any necessary prefactor before dependent work.
- [ ] Provide standalone plugin discovery, migrations, admin navigation and persistent account/plan forms; manual administration works without Organizations or Moyasar credentials.
- [ ] Use SAR integer halalas, monthly/annual immutable price versions, one personal account per user, and archived rather than rewritten prices; never seed sellable invented prices.
- [ ] Enforce general-administrator authorization at handler/API boundaries; organization roles cannot confer staff privileges.
- [ ] Document the one-way Organizations-to-Billing dependency, entitlement response, capacity-lock interface and Team capability gate; Billing must not import organization models.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

None (can start immediately).

