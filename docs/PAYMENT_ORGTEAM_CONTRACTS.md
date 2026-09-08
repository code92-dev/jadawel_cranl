# Billing and organization extension contracts

Reviewed against base a7d171a plus the pre-existing local checkout. This document distinguishes verified hooks from pending enforcement work.

## Confirmed packaging

The backend settings loader discovers plugin folders under JADAWEL_PLUGIN_DIR containing backend/, appends folder names to INSTALLED_APPS and invokes package.config.settings.settings.setup. Billing registers the `jadawel_billing` Plugin from BillingConfig.ready; API namespace is `api:jadawel_billing` with `/api/billing/` prefix. Startup performs no queries or network calls.

The Nuxt 3 module registers an admin type after the `core` plugin, adds `/admin/billing` and registers ar/en locale files. Installer frontend folder spelling is `jadawel-billing`. Module loading during production still requires verification. The installer Git source expects one plugin per archive/repository package; ship separate artifacts for the two plugins.

## Confirmed authority hooks

Existing administrative endpoints use DRF IsAdminUser. Billing additionally checks authenticated, active, staff at mutation-handler boundaries. Staff billing authority does not create workspace data access. Existing workspace roles are not organization roles.

CoreHandler.check_multiple_permissions iterates PERMISSION_MANAGERS and accepts the first definitive decision. Organization restrictions must register before permissive managers. CoreHandler.filter_queryset independently applies supported managers; direct checks alone cannot prevent list leaks. A manager must implement both the needed check and list behavior. The organization manager also handles the global `create_workspace` operation because that operation has no workspace context.

Verified core operations include workspace.read, workspace.create_application, workspace.create_invitation, workspace.list_workspace_users, workspace_user.update/delete, invitation.read/update/delete and application.read/update/duplicate/delete. Row operations include database.table.read_row, read_adjacent_row, update_row, move_row, delete_row, restore_row and read_row_history. The operation registry, not string heuristics, must define restricted-mode coverage.

The existing Viewer manager only denies view-configuration writes. It is not sufficient proof of read-only rows. The organization adapter must explicitly cover row/data writes.

Before workspace-user update/delete signals exist; membership-added is a post-mutation signal. Seat enforcement cannot rely on the latter. Membership creation/invite acceptance and core API bridge points require transaction-aware verification before organization work is marked complete.

## Billing service seam

BillingAccount is the stable account identity; a personal account is unique per responsible user. Team accounts may be multiple. Price amounts/currency/interval are immutable through exposed handlers/APIs; changes create a new version. Availability alone can be edited. Audit records retain support actions.

Billing exports get_effective_entitlements, require_entitlement and lock_capacity. Organizations will register a capacity provider during startup and use the billing-account row lock for member acceptance/removal. Billing never imports Organizations. Current manual-grant result contains source, plan, seat_limit, capabilities, valid_until, revision and restriction_reason. Reads check expiry directly, without cache. Paid subscription fallback is represented by the verified Subscription record; grace-period policy remains a later slice.

Manual grant changes replace their effective snapshot with audit before/after history. Suspensions have highest precedence. Current grants begin immediately through the UI; the API accepts explicit start dates. Review previews make no writes. Grants do not create financial transactions or cancel paid renewals.

## Moyasar research, 2026-09-08

- [Webhook reference](https://docs.moyasar.com/api/other/webhooks/webhook-reference): envelope contains id, type, secret_token, live and data. Verify shared secret and environment; retain only sanitized event fields. Server payment fetch remains required before granting paid access.
- [Webhook configuration](https://docs.moyasar.com/guides/dashboard/setting-up-webhooks): HTTPS endpoint and secret token; failed-event spelling includes payment_faild in the current guide.
- [Form configuration](https://docs.moyasar.com/guides/references/form-configuration): supports metadata, completion and initiating callbacks. Whether the chosen browser form supports a persisted given_id must be verified before selecting that flow; do not assume undocumented options work.
- [Payment idempotency](https://docs.moyasar.com/api/idempotency): UUID given_id represents one payment operation and is retained across uncertain retries.
- [Saved payment token](https://docs.moyasar.com/guides/tokenization/save-card-in-payment): token can be obtained before redirect but only verified successful payment/active token establishes usability.
- [Token charges/removal](https://docs.moyasar.com/guides/tokenization/tokenized-cards): active token required; token removal uses DELETE and successful removal returns 204.

## Remaining enforcement inventory before organization release

The organization adapter now registers both user and token actors and uses an
explicit allowlist of registered read operations; unknown operation names fail
closed for managed workspaces. The global workspace-creation check and optional
public-view policy are wired. Workspace bindings require a general administrator
to explicitly confirm a preview when existing outsiders are present. Assignments
support ADMIN, MEMBER, and read-only VIEWER enforcement. Workspace
attachment/import and delegated-job coverage still require dedicated integration
tests. Websocket page checks reuse the same CoreHandler operation path; public
view websocket access is denied when the optional public-view policy reports a
suspended or restricted organization. Any necessary core patch is narrow and
documented in PATCHES.md.
