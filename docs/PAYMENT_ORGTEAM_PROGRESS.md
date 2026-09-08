# Payment and organization implementation progress

Branch: `payment-Orgteam-plugins`. Executor: current Codex task (Luna handoff cancelled by user).
Review base: `a7d171a12de08174999adcf43f620b14569c08c0`.

## Tracker

All 20 approved vertical slices are published as GitHub issues #42–#61 in code92-dev/jadawel_cranl with `ready-for-agent` and native blocking edges. All 20 dependency sets were read back and verified. See PAYMENT_ORGTEAM_TICKETS.md. No issues closed; this branch contains the billing vertical slice only; no implementation has been pushed or deployed.

## Current work

- #42: standalone Billing backend discovery, account creation/listing, immutable price-version API and Arabic/English admin page implemented. Package metadata, README, migrations and registry/endpoint loading are present. Focused API/UI checks pass.
- #43: manual grant/update/revoke/suspension handlers and endpoints, audit, capacity lock and effective manual-access resolution implemented. Expiry, wrong-plan, capacity, suspension, paid fallback and server-side preview checks pass. Grace-period policy remains part of the renewal slice.
- #44: Individual checkout now creates an immutable server quote, sends card data directly to Moyasar, and activates access only after server verification of the provider payment ID, amount, currency, order metadata and successful paid status. Direct callback activation is not trusted. Paid orders return a verified receipt with provider reference and access period.
- #45: Moyasar adapter, idempotent webhook inbox, authenticated webhook environment checks, metadata/given-ID binding, leased/reclaimable Celery reconciliation and staff order/provider-event reconciliation views are implemented. Provider timeout, malformed responses, inactive payer recovery, mismatch failure, captured settlement, invalid-ID retry, webhook-before-callback recovery, duplicate event behavior and post-settlement reversal review have focused coverage.
- #46–#61: not implemented. Saved payment tokens, recurring renewals, refunds, organization members/workspaces, and production/browser sandbox evidence remain. The administrator procedure is documented in PAYMENT_ORGTEAM_ADMIN_MANUAL.md. No provider credentials were used and no payments were initiated.

## Test commands that work in this environment

From repository root (a local PostgreSQL dev instance is available at 127.0.0.1:5432; the test runner uses its own test database):

```bash
DATABASE_HOST=127.0.0.1 PYTHONPATH=backend/src:backend/tests:plugins/jadawel_billing/backend/src JADAWEL_PLUGIN_DIR="$PWD/plugins" backend/.venv/bin/python -m pytest -c backend/pytest.ini plugins/jadawel_billing/tests -q --reuse-db
```

Use `--create-db` after schema changes. Backend fixture setup is imported from the repository test utilities. `just` and `yarn` are not on this shell's PATH. System Node is 22; use the available Node 24 runtime below.

From web-frontend:

```bash
/home/aziz/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vitest/vitest.mjs --run test/unit/arabase/billingAdmin.spec.js test/unit/arabase/billingGrant.spec.js
```

Use the frontend Prettier config explicitly when formatting standalone files outside web-frontend.

## Verification recorded 2026-09-08

- Billing package tests: `30 passed` with the plugin's Django test command and a fresh schema.
- Repository backend fork gate: `402 passed, 1 skipped` in `backend/tests/arabase`.
- Repository frontend unit gate: `4443 passed, 8 skipped` across 156 files.
- Ruff, Ruff format, scoped mypy and `makemigrations --check --dry-run`: passed.
- Standalone Arabic/English locale parity: `86/86`; repository strict locale parity: `3787/3787`.
- `uv build --wheel` produced `jadawel_billing-0.1.0-py3-none-any.whl`; Nuxt `prepare` discovered the standalone module and generated types.
- Code review completed with two independent review passes. No live Moyasar credentials, charges, production deployment, or browser sandbox payment were used.

Production build and browser sandbox evidence remain blocked by the absence of provider credentials. The organization, renewal, token, and refund tickets remain open by design.

## Preservation

The pre-existing dirty files in manifests/locks, core settings/tests, PATCHES.md and page-document work are unrelated. Do not reset or stage them. Feature changes currently include plugins/jadawel_billing, the two billing UI test files, glossary additions, the plan and ticket index. The original plugin-creator skill directory was already untracked; do not silently include it in a feature commit.
