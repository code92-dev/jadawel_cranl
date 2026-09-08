# 18: Apply billing restrictions to organization access

## What to build

Organization access follows paid periods, grace, manual grants and capacity changes, with clear recovery messages.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Preserve authorized reading after payment grace but deny writes, invites, new workspaces and public publishing; billing recovery remains accessible.
- [ ] Apply suspension > manual > paid/grace precedence with cache invalidation and expiry-on-read; delayed events cannot override grants.
- [ ] Apply real membership usage to seat reductions and concurrent seat/grant changes; never evict arbitrarily.
- [ ] Enforce through existing APIs, tokens, realtime and background actors, not just plugin screens.
- [ ] Demonstrate failed renewal → restriction → payment recovery, grant expiry → paid fallback, and grant revocation without unexpected charging.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 16: Suspend, reactivate and archive organizations
- Draft 17: Activate organizations after Team payment
