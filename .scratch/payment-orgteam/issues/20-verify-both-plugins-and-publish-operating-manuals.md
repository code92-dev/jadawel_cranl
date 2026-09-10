# 20: Verify both plugins and publish operating manuals

## What to build

An operator can install, upgrade and operate both plugins using verified administrator/owner guides and complete acceptance evidence.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Run fresh/upgrade/restart combinations: Billing alone, both plugins, missing dependency, no provider config for free organization, existing retained data.
- [ ] Verify Arabic/English RTL/LTR, keyboard and mixed-direction values, pagination/error/empty states, SSR, production loading and standalone locale/test discovery.
- [ ] Run meaningful combined regression, concurrency and bypass checks plus repository-required locale/fork-hygiene gates; separate code failures from missing sandbox evidence.
- [ ] Complete manuals with actual UI labels/screenshots for free creation, grant edits/extensions/revocation, members/access, ownership, suspension, plans, payments/refunds, cancellation and provider health.
- [ ] Document pinned artifacts, migrations, upgrade/removal retention and fail-closed removal of enforcement; no automatic data purge or deployment.
- [ ] Keep custom roles, department teams, SSO/SCIM, usage pricing, coupons and automatic tax compliance out of v1; record explicit launch decisions and residual limitations.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 19: Guide Team-to-Individual transitions
