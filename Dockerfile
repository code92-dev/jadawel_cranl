# Deployment entry point for PaaS hosts that only support a root Dockerfile
# built from the repository (CranL, and others with the same constraint).
#
# It deliberately does NOT build the monorepo. The Nuxt production build peaks
# above 4 GB and is OOM-killed on a small app plan, so the image is built by
# .github/workflows/publish-image.yml on a GitHub runner and merely pulled here.
#
# Consequences of that split, in order of how likely they are to bite:
#
#   1. Pushing code does not change what is deployed. Run the publish workflow
#      first, then redeploy. A tag pinned below makes that explicit; `latest`
#      quietly deploys whatever was published last.
#   2. This is the `prod-lite` variant: no embedded Postgres or Redis. The host
#      must provide both, plus S3 for uploads — hosts without a persistent
#      volume lose container-local data on every redeploy.
#   3. The image serves on port 80 behind its bundled Caddy, not 3000.
#
# See docs/DEPLOY_CRANL.md for the full deployment procedure.

# Published 2026-09-16 from commit 0fb12bbe, tag
# 2.3.8-theme-boot-no-flash. Applies the interface theme before first paint to
# prevent a flash of the previous palette during startup.
# Previous deployment pin (2.3.7-white-theme-20260916):
# sha256:1f89d8fe78f43f86c5ce987c7445f394d6db5b8de2925df4d49a604d406a5ec4.
#
# 2.3.7-white-theme-20260916 aligned the white-theme workspace chrome.
# Previous deployment pin (2.3.6-billing-orgs-bundled):
# sha256:120dfcc493bed6435b499f7128d9c076817ae1aacd7701bce245116c7abc2533.
#
# 2.3.6-billing-orgs-bundled added the billing and organization Python packages,
# migrations, and Nuxt modules. The 2.3.5 image omitted these standalone plugins.
# Previous image pin (2.3.5-billing-orgs, incomplete plugin packaging):
# sha256:8e865d52238db1e1f1abbb794e26f6dd0023b5e848653e035da10775a9194d53.
# Previous deployment pin (2.3.4-kanban-grouping-dropdown):
# sha256:b17643feb1d24daa98921b7de1dc1cc35c6d01cb77b62558f8f16a73b5a5089d.
#
# The 2.3.4 deployment kept the kanban board's grouping-field dropdown at a
# full 240px width in the empty state instead of collapsing to icon width.
# Previous deployment pin (2.3.3-refresh-performance):
# sha256:6e95488e08c9fd2cfe47aa401468e0ea63a28cfd3cfc4693724fe5db8da2b725.
#
# Previously published 2026-09-06 from commit 274e7e2, tag 2.3.3-refresh-performance.
# Caches bundled translations across reloads and loads workspace/application
# startup data concurrently, including all changes through 2.3.2.
#
# Previously published 2026-09-03 by publish-image.yml from commit ca0573c (dependency
# updates), tag 2.9.18-deps-updates, digest
# sha256:4b6dfe69ae44c09bb43a07656ef0c32fd97acdcf09f88ad68963516e2eec38b5.
#
# 2.9.18-deps-updates carries the nine dependency updates verified by the
# 2026-09-03 regression gate on main: pyotp 2.10.0, typing-extensions 4.16.0,
# psycopg2-binary 2.9.12, cryptography 50.0.1, pytest-cov 7.1.0, tiptap
# extension-gapcursor 3.30.5, form-data 4.0.6, posthog-js 1.422.5 and
# vue-router 5.3.0. The happy-dom 20.11.15 bump is deliberately excluded: it
# breaks cookie isolation in the vitest suite (PR #25 stays open).
#
# The image moved from ghcr.io/azizahmed/jadawel_cranl to
# ghcr.io/code92-dev/jadawel_cranl when the repository transferred into the
# code92-dev organization. The package is public so CranL keeps pulling
# without registry credentials.
#
# Previously published 2026-09-03 by publish-image.yml from commit 08af13a
# (live canary release gates), tag 2.9.17-mcp-canary-gates, digest
# sha256:1c47e90074c69a58ee1e72d668b6303e053925a15cb601f3fec5fa19add31ccc.
#
# Previously published 2026-09-01 by publish-image.yml from commit ccadf39
# (responsive MCP settings modal fix), tag 2.9.16-mcp-mobile-modal, digest
# sha256:0310800c82f46c1c6a60ffef5c49122dc0843bb91e35d2c3a8be265f57852c41.
#
# 2.9.16-mcp-mobile-modal carries the responsive sidebar-modal fix on top of
# the 2.9.15 protected-field lifecycle/query-budget release and the 2.9.14
# capacity, artifact-boundary, dead-worker recovery, and Redis-outage hardening.
#
# Previously published 2026-09-01 by publish-image.yml from commit 8c49dd5
# (2.9.15-mcp-query-budget), digest
# sha256:b3564da531dd8af33566534f0a5117ae888946063ff70cbb5a156351bd050fac.
#
# Previously published 2026-09-01 by publish-image.yml from commit 3df47be
# (2.9.11-mcp-admin-summaries), digest
# sha256:8b6ddba8252f8e85956d47751374889d96321e0cfa59e91cfee6e3a3ec743421.
#
# 2.9.11-mcp-admin-summaries adds ownerless-admin protection summaries, blocks
# unsupported protected-field type conversions, hardens readiness with a bounded
# Redis canary and token headroom check, and ships the loading/conflict/read-only
# Arabic-first protection UX and responsive coverage.
#
# Previously published 2026-08-31 by publish-image.yml from release 2.9.8 @
# 0c21e63,
# digest sha256:5c03b0e117e1e2edeae6d2d8febb8bb990a9dddde225c59cd4ddf7e9ccf737b3.
#
# 2.9.8 allows the MCP policy idempotency header through cross-origin
# preflights so CranL's preview hostname can save protected-field policies to
# the canonical Jadawel API.
#
# Previously published 2026-08-24 by publish-image.yml from release 2.9.5 @
# 3f28dfc,
# digest sha256:5cb6e5ac7c0001dcf00106e00903a5d8dada5b86b2d794111afdf0ab690e4b90.
#
# 2.9.5 keeps private dashboard data-source configuration out of anonymous API
# responses while letting summary widgets render the safe aggregate result.
# This removes the public-dashboard SSR 500 without weakening share isolation.
#
# Previously published 2026-08-24 by publish-image.yml from release 2.9.4 @ 81827c1,
# digest sha256:be3bb8ec43803377a7515df5cb2e19ee5671184bb7860cb68f60b9c5064ea1c7.
#
# 2.9.4 normalizes the configured embedded-share base URL before joining the
# public dashboard route, so both base URL forms render and copy the same
# single-slash link. The focused component regression covers both forms.
#
# Previously published 2026-08-24 by publish-image.yml from release 2.9.3 @
# 779aaab, digest
# sha256:5d5c56e13f794f3cfb4d8ed118d338cdbe80c0e06c8cb26ad43768861428200b.
#
# 2.9.3 is the desktop-browser production-readiness release. It fixes malformed
# shared-dashboard API URLs and public positioning crashes, makes the default
# local template selectable again, hardens archive imports, raises backend
# keep-alive above Node's pooled-socket lifetime, and runs two bounded Nitro
# workers. Its release gate covered the full backend/frontend suites, Chrome
# and Firefox E2E, and two 600-request production-load phases with zero errors.
#
# Previously published 2026-08-22 by publish-image.yml from release 2.9.2 @
# 8f38f549d, digest
# sha256:f2a9aca605656e3361b19baedb866fd883a9fd46fa74aa3985341c02c49d7659.
#
# 2.9.2 makes the database-backed template catalog a startup invariant. It
# disables core's broad 150+ template sync, constrains any older queued task to
# the six local slugs, and reconciles synchronously after migrations. A
# successful startup therefore cannot expose the stale upstream catalog.
# User workspaces are not part of the cleanup, and later restarts are a no-op.
#
# Carried over from 2.9.0, matched Arabic and English project-management
# templates, plus Arabic and English Saudi budget-consolidation templates. It
# also enforces the Gregorian Arabic month names familiar in Saudi Arabia and
# clears Vite's generated dependency cache when correcting the datepicker locale.
#
# Previously published 2026-08-17 by publish-image.yml from tag v2.8.1 @
# c3639cd64, digest
# sha256:1047c4c1658496d8b94be17ec1eb7e00a6d5f2beff0bad4c44b8afad44bbba6e
#
# **No migration.** 2.8.1 changes one package in the image and one path lookup
# in the backup code.
#
# 2.8.1 makes backups possible at all. The image installed postgresql-client
# from POSTGRES_VERSION, the same variable that selects the *embedded* Postgres
# server, so it shipped pg_dump 15 — and this deployment backs up CranL's
# managed Postgres 16, which pg_dump refuses to touch because it will not dump
# a server newer than itself. Every backup failed on the version check.
#
# POSTGRES_CLIENT_VERSION=18 is now separate from POSTGRES_VERSION=15. Raising
# the latter would have fixed the dump and broken the image for anyone using
# the embedded database: a Postgres 16 server will not start on a data
# directory that 15 initialised. Newer is free for the client, which reads
# older servers and refuses only newer ones.
#
# Installing a newer client is not sufficient on its own. /usr/bin/pg_dump is
# Debian's pg_wrapper, which picks a major version from the default *cluster*
# — the embedded one — rather than from the server being contacted, and the
# prod stage still carries client 15 as a dependency of postgresql-15. So
# arabase.backup.runner.client_binary() reads /usr/lib/postgresql/*/bin/ and
# takes the highest major itself. pg_restore resolves the same way: a dump
# written by a newer pg_dump is unreadable by an older pg_restore.
#
# Carried over from 2.8.0, the Page view, a fourth view type beside Grid,
# Gallery and Form.
# A Page renders an HTML document written by an AI over MCP, fed with the
# view's live rows, and shares on a public link with the optional password a
# form already had. A new Page opens on a setup panel carrying the workspace's
# MCP address, the page's own number and a prompt to paste, because a page is
# authored from outside the app and an empty one is otherwise a dead end.
#
# The document is untrusted, so it never renders on the app's origin: it goes
# in an iframe sandboxed to allow-scripts *without* allow-same-origin, under a
# server-computed CSP whose connect-src is 'none'. The page is handed real
# rows, so what matters is that it cannot send them anywhere. See
# docs/PAGE_VIEW.md.
#
# Carried over from 2.7.2, the Backup admin section (Admin -> Backup): health,
# an hourly/daily/weekly schedule stored in the database rather than the
# environment, run history including failures, and a restore that will not
# write over the live database.
#
# 2.7.2 also fixed the Arabic date locale. `ar` was never imported into moment, so
# every date in the product rendered in Ukrainian — `serp` for August — because
# `uk` was the last import and moment answers a missing locale by keeping the
# one it is on. Digits stay Western, as AGENTS.md requires.
#
# Carried over from 2.7.0, the two that matter most in production:
#
#   - A public dashboard link returned every column of its backing table, not
#     just the ones its widgets display. Anyone holding a share URL could read
#     the rest of the row. Existing links keep working and are now scoped.
#   - Backup retention listed by prefix and deleted anything past the window,
#     so an empty JADAWEL_BACKUP_S3_PREFIX meant the whole bucket. The config
#     now refuses an empty prefix, which means a backup job configured that way
#     will fail loudly on this image instead of running.
#
# Also: rate limits are countable per client (they keyed on a caller-controlled
# header before, so the contact form was an open mail relay), disabled MCP tools
# can no longer be invoked by name, share tokens expire, chart and agenda
# widgets read date columns correctly, and user files are archived alongside the
# database dump.
#
# Set JADAWEL_* in the dashboard before deploying. The BASEROW_* shims still
# accept the old names, but JADAWEL_JWT_SIGNING_KEY must carry the same value
# as BASEROW_JWT_SIGNING_KEY or every issued session is invalidated.
#
# JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=yes is worth setting here: it is what
# turns on Secure cookies and HSTS, and the all-in-one image defaults it empty.
#
# Pinned by digest, not by tag. The publish workflow pushes `:latest` alongside
# the version tag, so a tag pin does not identify a fixed image. The digest
# does, and it is the release build described above.
#
# Changing only this line has not been enough to swap the container: CranL
# reported the 2.7.2 deploy `done` while the old workers kept running, because
# a digest-only edit to a `FROM` does not invalidate its build cache. Follow
# the deploy with a reload, and verify behaviour rather than trusting `done`.
ARG JADAWEL_IMAGE=ghcr.io/code92-dev/jadawel_cranl@sha256:7b00d5320e4d2606054744516197b5c10b65945fd3217c61173b2b1a76d5c8c0

# hadolint ignore=DL3006
FROM ${JADAWEL_IMAGE}

# The portable image defaults to one Nitro worker so it remains safe under its
# documented 768 MB frontend cap. CranL has a 4 GB whole-app allocation, and
# the two-worker production benchmark removes single-process SSR queueing while
# keeping aggregate frontend RSS bounded at roughly 1.3 GB.
ENV NITRO_CLUSTER_WORKERS=2

# Inherited from the base image and repeated here only so the deployment target
# is readable without chasing the base: ENTRYPOINT ["/jadawel.sh"], CMD ["start"].
EXPOSE 80
