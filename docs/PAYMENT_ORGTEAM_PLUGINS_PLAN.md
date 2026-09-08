# Moyasar billing and organization plugins — Luna execution plan

Status: approved; implementation complete in the working tree, release gates
remain. Date: 2026-09-08.
Branch: `payment-Orgteam-plugins`. Base: `a7d171a12de08174999adcf43f620b14569c08c0`.
Executor: current Codex task, per user instruction. Use implement, TDD and code-review skills; commit feature work to this branch. Do not deploy.

## 1. Confirmed requirements

- Two distinct installable Jadawel plugins: billing first, organizations second.
- Billing supports Individual and Team subscriptions through Moyasar.
- A Team organization contains multiple users and owns workspaces. It is not a department or a group within a workspace.
- Organizations provide invitations, member removal, role assignment, and workspace access management.
- The Jadawel general administrator can create an organization without payment and manually assign, edit, extend, and revoke access, plans, and seats.
- Deliver Arabic-first and English UI, administrator instructions, installation instructions, and verified behavior.
- The user approved the 20-ticket breakdown and requested implementation and commits through the implement skill. GitHub issues are #42–#61. No live charges or deployment are authorized.

## 2. Proposed defaults and launch decisions

These are implementation defaults, not user-confirmed commercial terms. Build configurable settings; never invent live prices.

| Topic | Proposed implementation default |
| --- | --- |
| Currency and intervals | SAR; monthly and annual price versions; money stored as integer halalas |
| Team pricing | Price per purchased seat; owner counts as one seat; minimum one |
| Seats | Active members consume seats; pending invites do not; acceptance locks and rechecks capacity |
| Multiple accounts | A user can retain a personal account and belong to multiple organizations |
| Leadership | Exactly one organization Owner; any number of Administrators and Members |
| Invitations | Expire in 7 days; resend rotates the token; accept only as the matching verified email |
| Suspension | Suspended membership retains its seat; removal releases it |
| Failed renewal | Proposed 7-day grace, retries after 1 and 3 days; then restricted access |
| Restricted subscription | Preserve reading for already authorized members; deny data writes, invitations, new workspace creation, and public publishing; billing recovery stays accessible |
| Seat increases | Pay a server-calculated prorated amount before granting extra capacity |
| Seat reductions | Schedule for renewal; reject reductions below active plus suspended membership |
| Cancellation | Stop future renewals, retain access through paid period; no automatic refund |
| Team to Individual | Guided move to personal billing after organization workspaces are explicitly resolved; no automatic workspace transfer or data deletion |
| Existing installation | No automatic paywall, ownership transfer, or migration of existing workspaces |
| Manual access | Explicit administrator grant with plan, seat cap, start, optional expiry, reason, and actor |

Before live checkout: obtain actual prices, tax/invoice treatment and business details, refund policy, grace/retry approval, merchant-enabled payment methods, and recurring-payment eligibility. These do not block schema, manual management, mock-provider tests, or sandbox development. Do not label ordinary payment receipts as compliant tax invoices without an approved invoicing solution.

## 3. Packaging and dependency contract

Create `plugins/jadawel_billing/` and `plugins/jadawel_organizations/` using the named skill's standalone packaging reference. Each has `jadawel_plugin_info.json`, a pip-installable backend, a Nuxt 3 module, translations, migrations, tests, and README.

- Python/plugin types: `jadawel_billing`, `jadawel_organizations`; first check collisions.
- API prefixes: `/api/billing/`, `/api/organizations/`.
- Frontend module directories: `jadawel-billing`, `jadawel-organizations`.
- Billing loads and works for Individual accounts without Organizations.
- Organizations requires Billing for the entitlement contract, but never requires Moyasar keys or a paid subscription for administrator-provisioned organizations.
- Billing must not import organization models. Organization has a unique foreign key to a Team billing account.
- Expose a feature-capability registration from Organizations so Billing hides self-service Team checkout until organization provisioning is installed and healthy.
- Pin compatible plugin revisions. Missing Billing prevents Organizations startup with an actionable dependency error; do not silently drop permission enforcement.
- Uninstall/removal retains database data. Disable customer traffic to managed workspaces before removing enforcement code; uninstall must not turn protected workspaces into unrestricted workspaces.

Read `.agents/skills/jadawel-plugin-creator/SKILL.md` and both references before coding. Python 3.14, Django, Nuxt 3, Vue 3, Node 24; verify exact versions in manifests. No premium/enterprise dependencies. Prefer plugin registries. Necessary upstream-derived backend edits require a written hook-gap explanation and `PATCHES.md` entry.

## 4. Current repository map (verified starting points)

| Concern | Read first |
| --- | --- |
| Plugin/API registration | `backend/src/jadawel/core/registries.py`, `backend/src/arabase/apps.py`, `backend/src/arabase/plugins.py` |
| Existing membership and invitation data | `backend/src/jadawel/core/models.py` (`WorkspaceUser`, `WorkspaceInvitation`) |
| Membership authorization/mutations | `backend/src/jadawel/core/handler.py`, `backend/src/jadawel/core/permission_manager.py` |
| Existing API bypass surfaces | `backend/src/jadawel/api/workspaces/{users,invitations}/`, `backend/src/jadawel/api/admin/workspaces/` |
| Lifecycle hooks | `backend/src/jadawel/core/signals.py`; inspect call sites and transaction timing |
| Additive permission example | `backend/src/arabase/permissions/viewer_role.py` |
| General administrator example | `backend/src/arabase/api/backup/views.py` uses DRF `IsAdminUser` |
| Admin navigation | `web-frontend/modules/arabase/adminTypes.js`, `routes.js`, `registryPlugin.js` |
| Module and locales | `web-frontend/modules/arabase/module.js`, `roleTypes.js`, `permissions.js` |
| Existing members UI | `web-frontend/modules/core/pages/settings/members.vue` and referenced `MembersTable` |
| Runtime/package discovery | `deploy/plugins/`, backend settings loader, frontend Docker entrypoint, Nuxt base config |

Core signals include before-update/delete membership hooks, but the membership-added signal is post-add. Do not assume these signals alone cover all authorization or seat races. Inspect permission operation coverage before choosing an adapter.

The checkout was dirty before planning (including manifests, settings, PATCHES.md, frontend page tests, and the untracked plugin skill). Preserve these changes. They are not part of this plan. Re-read `git status --short` before each implementation chunk; do not stage or reset unrelated files.

## 5. Data model and service boundaries

Proposed model names below are new, not existing Jadawel APIs. Make schema details concrete in B01 before writing dependent code.

### Billing-owned data

- `BillingAccount`: UUID, kind INDIVIDUAL/TEAM, responsible user, lifecycle status. One personal account per user; multiple Team accounts allowed. Changing payer does not silently transfer organization ownership.
- `Plan` and immutable `PlanPrice`: code, interval, currency, amount, included capabilities, sale availability. Archive prices; never rewrite amounts on past purchases.
- `Subscription`: account, price snapshot/reference, purchased seats, period boundaries, state, cancel-at-period-end, pending change, recurring consent. At most one current subscription per account.
- `BillingOrder`: immutable expected amount/currency/account/purpose/period/seat change, status, expiry. Every payment is bound to one order.
- `PaymentAttempt`: order, unique provider payment ID and stable operation UUID, status, verified timestamps, sanitized failure. Test/live namespace isolation.
- `SavedPaymentMethod`: account-scoped provider token reference, safe display metadata, activation state, consent. Never store PAN/CVC or expose usable tokens.
- `ProviderEvent`: deduplication identity, sanitized payload/summary, processing state, retry count. Never persist the webhook secret in payloads.
- `ManualEntitlementGrant`: account, explicit feature/seat replacement, start/end, reason, actor, revocation. At most one effective grant; edits produce an auditable revision.
- `BillingAuditEvent`: actor/system, action, target, sanitized before/after, reason, timestamp, correlation ID. No customer mutation endpoint.
- Receipt and refund records reference original payments; refund attempts have their own operation identity and reconciliation status.

### Organization-owned data

- `Organization`: UUID, unique Team account, name, lifecycle state; owner represented by the membership invariant.
- `OrganizationMember`: unique organization/user, OWNER/ADMIN/MEMBER, ACTIVE/SUSPENDED. Protect the sole owner and coordinate ownership transfer transactionally.
- `OrganizationInvitation`: normalized email, hashed token, expiry, inviter, requested role, accepted/revoked status. Prevent multiple usable invitations for the same organization/email.
- `OrganizationWorkspace`: unique workspace link, organization. A workspace belongs to at most one organization.
- `WorkspaceAccessAssignment`: organization membership, linked workspace, core role ADMIN/MEMBER/VIEWER. Unique membership/workspace pair; synchronize through core handlers.
- `OrganizationAuditEvent`: invitations, access changes, suspensions, removals, ownership changes, organization lifecycle.

Retain financial and audit history when users leave. Choose protective/nulling foreign-key behavior explicitly; account or organization removal must not cascade-delete payment evidence or workspace data.

### Public internal contract

Billing exports `get_effective_entitlements(account_id, at)`, `require_entitlement(account_id, capability)`, and a capacity-lock context/service used by organization membership mutations. Result contains source, plan, seat_limit, capabilities, valid_until, restriction reason, revision.

Precedence: explicit general-admin suspension > valid manual grant > valid paid subscription/grace > restricted/unprovisioned. Manual grants replace the relevant entitlement snapshot, not add unlimited seats. Expiry/revocation falls back to the current paid subscription if valid. Provider events can update payment facts but never delete or overwrite a manual grant.

Manual grants do not silently cancel an existing paid renewal. When granting free access to an already-paying account, show its renewal state and provide a separate explicit stop-renewal action. Starting paid billing from manual access requires payer consent and a new verified order; removing a grant must never trigger an unexpected charge.

Invalidate entitlement caches after commit; check expiry on reads. Do not hold a database transaction across provider HTTP calls. Use durable pending operations/outbox work and reconciliation around external side effects.

## 6. Authority and access matrix

| Action | General admin | Org owner | Org admin | Member |
| --- | --- | --- | --- | --- |
| Create free organization / manual grants | Yes | No | No | No |
| Edit live plan catalogue | Yes | No | No | No |
| Pay/manage own account subscription | Admin support actions audited | Yes | No | No |
| Invite/remove Members; assign workspace access | Yes | Yes | Yes, within authority | No |
| Appoint/remove organization Admin | Yes | Yes | No | No |
| Transfer ownership | Yes, audited | Yes, to active member | No | No |
| Suspend/archive organization | Yes | Archive with retention policy | No | No |
| Read workspace data | Existing explicit data authority | Assigned workspace role | Assigned workspace role | Assigned workspace role |

Use the installation's existing general-administrator predicate, verified against existing admin endpoints; current example is `IsAdminUser` (`is_staff`). Organization roles must never set Django staff/superuser flags. Repeat authorization at handler boundaries for jobs/API callers. General-admin management authority does not by itself add blanket data-reading access.

For managed workspaces, organization membership/access records are authoritative. Route legacy member/invite mutations through the same adapter, or reject with a specific managed-workspace error. Do not allow a workspace admin to add non-organization users through old endpoints. Existing unmanaged workspaces remain unchanged.

Suspend/remove membership must revoke managed workspace access immediately, including cached permissions, API-token paths, websocket updates, automation and integration actors where they act on behalf of that user. Preserve unrelated organizations and personal workspaces. Inventory user-owned credentials and scheduled actors; do not assume UI logout covers them. Define public links independently: removing a member cannot revoke information intentionally published publicly. Organization suspension disables public sharing on its workspaces without deleting share configuration.

## 7. Moyasar integration contract

Use Moyasar's supported browser form/SDK for card entry directly to Moyasar and backend secret-key calls for verification. Do not assume a Stripe-style hosted subscription/customer portal exists. Jadawel owns the subscription schedule unless an actual supported merchant API is verified.

Official sources checked 2026-09-08:

- [Authentication and test/live keys](https://docs.moyasar.com/api/authentication): secret keys stay server-side; card details must not pass through Jadawel's backend.
- [Payment creation idempotency](https://docs.moyasar.com/api/idempotency): use a persisted UUID `given_id`, retaining it across uncertain retries of the same operation.
- [Payments reference](https://docs.moyasar.com/category/payments-api): fetch status and use provider-supported refund operations.
- [Tokenization](https://docs.moyasar.com/category/tokenization): saved tokens can support future charges; verify active state and account capabilities.
- [Dashboard configuration](https://docs.moyasar.com/category/dashboard): follow linked current webhook setup documentation during B04; exact authentication/event envelope remains to be verified in sandbox.

Server computes the order quote. Redirect query parameters and browser callbacks never activate access. Authenticate webhooks using the documented current mechanism, fetch the payment from Moyasar, and check provider ID, amount, currency, environment, order association, and successful settled status before activation. Reject reusing a payment for another order. Authorized/initiated does not equal paid.

Persist authenticated events before acknowledging; processing is retryable. Duplicate deliveries, callback/webhook races, and old events must not double-activate or regress newer state. Reconciliation fetches uncertain or missing results using the original identifier. After an unknown charge result, do not create a new charge identifier until the previous attempt is resolved.

Store recurring consent; confirm each token belongs to the account via the verified payment flow. Model challenge-required renewals as customer action, not endless automatic retries. Refunds are general-admin actions with reason, amount validation and confirmation; payment truth remains immutable. Use provider-documented refund idempotency if available, otherwise reconcile uncertain refunds before retrying. A refund does not silently revoke an independent manual grant.

Proposed environment names: `JADAWEL_MOYASAR_SECRET_KEY`, `JADAWEL_MOYASAR_PUBLISHABLE_KEY`, `JADAWEL_MOYASAR_WEBHOOK_SECRET`, `JADAWEL_BILLING_MODE`, `JADAWEL_BILLING_LIVE_ENABLED`. Finalize in B04 after checking conventions. No hardcoded keys or secret input in admin UI; expose configuration health only. Sandbox first, live charging off by default. Manual management must function with all Moyasar variables absent.

## 8. Screens and administrator manual requirements

Customer: personal billing; organization billing; checkout/result; payment methods and consent; history/receipt; organization overview; people/invitations; workspace access; organization settings. Paginate searchable lists, show loading/empty/error states, and make restricted/complimentary status understandable.

General administrator navigation: Billing (plans, accounts, subscriptions, payments/refunds, manual grants, reconciliation) and Organizations (create/edit, owner, members, workspace assignment, suspend/reactivate/archive, history). Display payment state and effective access separately, with the reason for the effective access.

Create `docs/PAYMENT_ORGTEAM_ADMIN_MANUAL.md` during implementation, using real verified labels and screenshots. It must include these end-to-end procedures:

1. **Create without payment:** Admin → Organizations → Create → name + existing owner or owner email → Complimentary Team access → seat cap + optional expiry + reason → review → create. Atomic account/grant/organization creation; zero provider calls. For a new owner, issue a restricted setup invitation, reserve the owner seat, and leave the organization pending until accepted. General admin can resend/reassign pending ownership.
2. **Assign/edit plan or seats:** open billing account → manual access → preview before/after and current renewal behavior → save with reason. Do not fake a paid transaction. Below-usage caps show conflict and resolution steps, not arbitrary eviction.
3. **Extend/revoke access:** set expiry or revoke grant → preview fallback paid/restricted state → confirm; verify effective entitlement and audit record.
4. **Manage people:** add an existing user manually or invite a new one, assign role/workspaces, suspend/reactivate/remove; retain data. Never set another person's password through this flow.
5. **Transfer ownership:** select active member → verify successor → change organization owner and explicitly review payer responsibility.
6. **Suspend/reactivate/archive:** preview affected organization access and separately stop future renewals if desired; preserve records and workspaces. No permanent deletion button in v1.
7. **Record external payment:** optional admin record with amount/date/reference/reason, labelled external and unverified by Moyasar; grant access separately. Do not include it as Moyasar revenue.
8. **Refund/reconcile:** show provider payment, refundable balance, reason, result/uncertain state; prevent duplicate attempts. Explain that editing an entitlement does not refund money.
9. **Configure plans/provider:** create new price versions, archive old prices, configure secret environment values externally, check sandbox health, and follow a separate live-release checklist.

Add an owner guide for invitations, seat purchases, cancellation and workspace assignments. Validate Arabic RTL, English LTR, keyboard operation, mixed-direction email/payment IDs, confirmation focus, and accessible status messaging using the RTL skill during UI implementation.

## 9. Ordered work packets for Luna

One packet per implementation turn unless trivially small. Read only its dependency outputs and relevant source. Finish a packet's tests before starting the next. All paths below are proposed additions. For each packet record files, checks/results, next packet and blockers in `docs/PAYMENT_ORGTEAM_PROGRESS.md`. Do not mark planned checks as passed.

### B00 — Discovery and contracts (no feature implementation)

Read sections 1–7, skill/references, current manifests, root/nested guidance and git status. Inventory permission operations, workspace mutation/creation/import paths, realtime and token actors, plugin task discovery and test setup. Write `docs/PAYMENT_ORGTEAM_CONTRACTS.md` with exact hook names, allow/deny operation lists for restricted access, API error/status conventions, proposed migrations and remaining provider questions. Explicitly record any hook gaps. Exit: every enforcement surface has a concrete integration point or a narrowly scoped core patch proposal; never claim an unverified hook exists.

### B01 — Billing package and account schema (depends B00)

Create `plugins/jadawel_billing/{jadawel_plugin_info.json,backend/pyproject.toml,README.md}` and backend `src/jadawel_billing/{apps.py,plugins.py,models.py,migrations/,config/settings/settings.py,api/urls.py}`. Add registry loading, model constraints, immutable price/order snapshots. Exit tests: plugin lookup and namespaced endpoint, migrations, duplicate-account/current-subscription constraints; Billing starts without Organizations or Moyasar config.

### B02 — Entitlements and administrator grants (depends B01)

Add backend `entitlements.py`, `handlers.py`, `permissions.py`, `api/{views,serializers}.py`, audit models/services. Implement precedence, capacity locking, lifecycle and manual Individual/Team grants. Exit tests: staff allowed, ordinary/org admin denied, expiry boundary, paid fallback, suspension override, audit before/after, no provider calls, concurrent grant edits and seat mutations serialized.

### B03 — Billing admin UI and manual workflow (depends B02)

Create billing `web-frontend/package.json`, `modules/jadawel-billing/{module.js,plugin.js,adminTypes.js,routes.js,services/,pages/,components/,locales/}`. Register translations and admin navigation. Implement accounts/plans/manual access UI, with explicit renewal status and confirmation. Exit: a staff user assigns/edits/revokes manual access in the browser; ordinary user denied by direct API as well; Arabic/English render and labels pass parity.

### B04 — Moyasar adapter, order verification and events (depends B02)

Add `providers/moyasar.py`, order handlers, event inbox/reconciliation task, provider configuration. Consult env-var skill if wiring common settings. Verify official webhook schema/authentication, payment statuses, HTTP timeouts and current SDK integration; record sources in contracts. Exit tests: forged/duplicate/out-of-order webhook, wrong amount/currency/order/environment, reused payment, timeout/retry same ID, DB failure after provider success. Sandbox evidence must include server-verified successful and failed payment. Missing credentials block sandbox evidence only, not unit work.

### B05 — Customer checkout and history (depends B03,B04)

Add Individual/Team selection, server quotes, Moyasar form, result polling, payment history and receipt view. Gate Team purchase until Organizations capability is present. Exit: browser callback alone cannot activate; abandoned/3DS failure has a recovery path; no card data hits Jadawel; other account receipts/tokens are denied. Price fixtures are test-only and unsellable by default.

### B06 — Subscription renewal and payment methods (depends B04,B05)

Add token lifecycle, consent, subscription state machine and Celery schedule using verified discovery. Lock renewal periods; one charge attempt identity per logical operation. Implement failed/unknown/challenge-required outcomes, grace/retry and recovery. Exit with controlled-clock tests: duplicate workers, month-end/leap-year dates, restart after charge, revoked token, missing webhook, cancellation racing a renewal. No renewal is charged from an expired/manual-only grant.

### B07 — Subscription changes and refunds (depends B06)

Add prorated seat increases, scheduled reductions/cancellation, plan changes, staff refund and external-payment record UI/API. Document rounding and UTC period math; snapshot every quote. Exit: capacity only increases on verified success; duplicate refunds prevented; current receipts remain unchanged after price edits; restrictions recover on payment; manual grants survive unrelated events. Complete Billing installation/upgrade guide and focused regression gate before organization work.

### O01 — Organization package and manual provisioning (depends B02,B07)

Create `plugins/jadawel_organizations/` with equivalent packaging and backend `src/jadawel_organizations/{apps.py,plugins.py,models.py,migrations/,handlers.py,api/,config/settings/settings.py}`. Add organization/account one-to-one linkage, owner invariant, pending-owner setup flow and lifecycle. Exit: admin creates free organization without keys/network calls; repeated create request returns the same organization; Billing still loads alone; missing Billing fails clearly.

### O02 — Members, invitations and ownership (depends O01)

Add invitation/token handlers, member roles, audit, emails sent after commit and idempotent acceptance. Use existing auth/email infrastructure; no second user identity system. Exit: concurrent last-seat acceptance permits only one member; email mismatch/expired/replayed invite denied; owner removal forbidden; admin cannot self-promote; two organizations remain isolated. Apply capacity rules to direct admin additions too; explicit grant edit is the way to expand capacity.

### O03 — Workspace access adapter and enforcement (depends O02)

Implement B00's exact permission hooks, operation registration, core-handler bridge and permission invalidation. Bind new workspaces; attach existing ones only through general-admin preview that accounts for every existing member and pending invitation. Reject unresolved outsiders rather than silently stripping access. Exit: plugin and legacy APIs, import/copy/create, API tokens, public shares and realtime honor organization rules; no seat bypass; suspension/removal revoke managed access; personal workspaces unaffected. Log any essential core edits in PATCHES.md.

### O04 — Organization customer and general-admin UI (depends O03)

Create organization Nuxt module, admin types, routes, services, pages/components and locales. Implement overview, people, invitations, roles/workspaces, owner transfer, lifecycle and the free-creation wizard. Exit: test the manual's create/edit/invite/remove/suspend/reactivate flows in Arabic and English, including keyboard/error/empty states and direct-URL permission denial.

### O05 — Paid Team activation and lifecycle integration (depends O04)

Register Team capability. Use a durable provisioning action after verified Team payment so crash/retry cannot lose a paid organization or create duplicates. Handle owner setup, subscription restrictions/recovery, grant expiry, seat changes and guided Team-to-Individual transition. Exit: paid → organization ready; paid but provisioning failed → visible retryable pending state; manual free → paid requires consent; downgrade never orphans workspace ownership or erases data.

### V01 — Integration, packaging and documentation (depends O05)

Write the administrator manual and owner guide with actual UI screenshots; complete README install/upgrade/remove and dependency instructions for both plugins. Install into disposable compatible images: Billing alone, both plugins, absent provider config with manual access, fresh DB and existing-data upgrade, restart, migrations and frontend build. Verify actual locale checker coverage for standalone directories; add focused coverage if needed. Audit remaining work against section 10 and report blockers honestly. Do not deploy without a later user instruction.

## 10. Verification checklist and commands

- [ ] Individual sandbox payment/renewal/cancellation and failed-payment recovery.
- [ ] Team sandbox payment, crash-safe provisioning and purchased-seat enforcement.
- [ ] General admin creates free organization with absent Moyasar configuration; assigns/edits/extends/revokes access and audits it.
- [ ] Manual overrides and provider facts remain independent under delayed events.
- [ ] Organization role matrix, last-owner protection, workspace isolation, original API bypass tests and immediate revocation.
- [ ] Concurrent invitation acceptance, renewal, seat update and ownership transfer tests use a real transactional database.
- [ ] Refund uncertainty/idempotency, immutable history and test/live isolation.
- [ ] Existing unmanaged workspaces and personal access stay unchanged.
- [ ] Arabic/English parity, visible RTL/LTR, keyboard behavior, SSR and production build.
- [ ] Fresh install, upgrade with retained data, restart and dependency failure tested in disposable images.
- [ ] Administrator manual matches the implemented screens; prices and merchant production settings remain explicit launch inputs.

Consult backend/frontend test skills when creating tests. Tests belong in each plugin package; wire backend Django settings/fixture imports and frontend Vitest aliases explicitly in B00/B01. Verify commands before running; do not assume root runners discover external plugin tests.

Existing repository gates:

```bash
just b test tests/arabase -q
just f yarn locale:check
just f lint
just b lint
```

Use focused plugin tests for each packet, then one appropriate combined regression suite at V01. Read justfiles to establish exact plugin-test invocation and record it in each README. Locale parity and fork hygiene are required before any later requested push. Lint only changed paths during packets where supported. Do not count a command that skipped plugin tests as verification.

## 11. Resume prompt for the implementation agent

> Follow the approved GitHub ticket frontier in PAYMENT_ORGTEAM_TICKETS.md. Work on branch `payment-Orgteam-plugins`. Read AGENTS.md, the jadawel-plugin-creator skill, docs/PAYMENT_ORGTEAM_PLUGINS_PLAN.md, and any progress/contracts files. Implement only the next incomplete work packet and its acceptance tests, preserving unrelated changes. Use the specified two-plugin boundary and manual-entitlement precedence. Do not invent APIs, commercial prices, or passing test results. Record actual paths, commands, outcomes and next packet in docs/PAYMENT_ORGTEAM_PROGRESS.md. Missing Moyasar credentials block only provider-dependent verification; continue independent work and mark it unverified. Commit reviewed feature work as requested by the implement skill. Do not deploy or charge real money. If a product choice blocks this packet, state the exact choice and continue independent work.

## 12. Deferred additions

Department teams, custom per-table/field role builders, SSO/SCIM, usage-based pricing, coupons, automatic tax compliance, accounting integrations and bulk CSV imports are outside v1. Permanent account/data deletion is outside both plugins' management UI. These can be separately planned without expanding Luna's current work packets.
