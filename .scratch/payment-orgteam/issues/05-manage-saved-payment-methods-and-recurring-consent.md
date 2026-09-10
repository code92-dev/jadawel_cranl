# 05: Manage saved payment methods and recurring consent

## What to build

A payer saves or removes a verified Moyasar payment method and explicitly controls recurring-payment consent.

Target integration branch: `payment-Orgteam-plugins`. Implement one vertical slice using the Jadawel plugin-creator skill and existing extension contracts. Include persistent behavior, backend authorization, usable UI and focused tests together. All user-facing changes require Arabic/English parity, RTL/LTR and keyboard verification. Preserve unrelated work and data; no live charges or deployment are authorized by this ticket. Draft status: awaiting breakdown approval; publish with `ready-for-agent`.

## Acceptance criteria

- [ ] Provide account-scoped method list, safe display details, save/remove and consent UI backed by verified token ownership and activation.
- [ ] Never expose usable tokens, PAN/CVC or log secrets; reject another account's token.
- [ ] Use actual merchant-supported tokenization capabilities, not an assumed hosted subscription portal.
- [ ] Inactive/revoked methods produce clear customer-action states; manual-only accounts never acquire automatic charging consent.
- [ ] Record actual verification results and update the relevant administrator/owner instructions for this slice; do not report unrun checks as passed.

## Blocked by

- Draft 03: Buy an Individual subscription with Moyasar

