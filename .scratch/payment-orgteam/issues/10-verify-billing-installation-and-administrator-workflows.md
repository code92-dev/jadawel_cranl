# 10: Verify Billing installation and administrator workflows

## What to build

Billing can be installed and upgraded independently, with a demonstrated admin/customer workflow and usable billing manual.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Test fresh install, migrations, restart, existing-data upgrade, absence of Organizations and absence of provider configuration for manual operations.
- [ ] Verify plugin test discovery, locale coverage, SSR/production build, fork hygiene and one focused billing regression gate.
- [ ] Document actual screens for plan versions, grants, cancellation, reconciliation, refunds, external records and provider configuration health.
- [ ] List live launch inputs: actual prices, tax/invoice treatment/business details, refund policy, grace/retry approval and merchant recurring capability; do not claim tax compliance.
- [ ] Pin installation artifacts and record outstanding sandbox/environment checks; do not deploy.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 08: Change plans and purchased seat capacity
- Draft 09: Refund payments and record external payments

