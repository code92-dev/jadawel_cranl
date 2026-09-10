# Deploying Jadawel to CranL

## Current production target (September 2026)

Production is `https://app.jadawl.site`, mapped in CranL to **jadawel-org**
(`8ff2d656-4fde-4513-adf3-6b9c20434867`, Saudi-5), whose default domain is
`jadawel-org-sudtap.cranl.net`. The older **jadawel** / `jadawel-img0kf.cranl.net`
app is not this production target. The root `jadawl.site` is the marketing site.
Deploy from `code92-dev/jadawel_cranl`, branch `main`.

Billing and Organizations are standalone plugins under `plugins/`. Their Python
packages must be installed in the backend production image, their Nuxt modules
compiled in the frontend image, and their backend discovery folders included in
the all-in-one-lite image. Committing the plugin sources alone does not install
them. The publish workflow checks their API routes and migrations before pushing.
Build them on GitHub; runtime frontend compilation exceeds the CranL memory budget.

After deploying the digest pin, use Actions → Reload and verify production health
plus `/api/billing/admin/plans/` and `/api/organizations/admin/`. Anonymous calls
to these administrator endpoints must require authentication, rather than return
`URL_NOT_FOUND`. Verify the admin pages with an authenticated administrator too.
Moyasar credentials and live-payment activation remain separate environment settings.

The older setup notes below describe the original deployment and retain historical
hostnames and repository ownership; use the current target above for releases.

## Which repository is this?

`Azizahmed/jadawel_cranl` — a deployment copy, originally branched from
`Azizahmed/Jadawel` at `codex/hostinger-coolify-deploy` and carrying the root
`Dockerfile` and `publish-image.yml` on top of it.

**This is now the only deployment.** The Coolify instance it was once kept
separate from, `jadawel.azoz.cloud`, has been switched off and will not be used
again; `codex/hostinger-coolify-deploy` is stale and nothing watches it.

Code changes belong in `Azizahmed/Jadawel`. To bring them here, fast-forward this
repository's `main` from the `origin` branch being released, then publish a new
image. Committing feature work directly here diverges the two trees with no path
back.

[DEPLOYMENT.md](DEPLOYMENT.md) describes the retired Coolify setup and applies to
nothing that runs. The differences that shape everything below:

- **No Docker Compose build pack.** The new-app wizard offers Railpack
  (auto-detect) and Dockerfile, nothing else. `docker-compose.yml` is unusable.
- **Railpack cannot build this repo.** It looks for an application manifest at
  the root; this is a monorepo whose manifests live in `backend/` and
  `web-frontend/`. Detection fails before any build step, with
  `Railpack could not determine how to build the app`.
- **Build type and branch are set only at creation.** The Settings tab exposes
  domain, port and delete; there is no update-application endpoint in the API.
  Changing either means creating a new app and deleting the old one.
- **4 GB RAM per app on Pro.** The Nuxt production build peaks above that, so
  building this repo on CranL fails regardless of configuration.
- **CranL terminates TLS and routes to the container itself.** No Traefik
  labels, no external proxy network, no certresolver — all of which the Coolify
  compose file exists to configure.
- **No persistent volume.** Anything written inside the container is lost on
  redeploy.

## The shape of the deployment

Because the app cannot be built on CranL, the build moves to GitHub Actions
(16 GB runners) and CranL only pulls the result:

```
push to branch
  -> GitHub Actions (publish-image.yml): backend + web-frontend -> all-in-one-lite
       -> ghcr.io/azizahmed/jadawel_cranl:<tag>
            -> root Dockerfile: FROM that image
                 -> CranL builds a trivial one-line image and runs it on :80
                      -> managed Postgres + managed Redis + S3
```

The `prod-lite` variant is used deliberately. The full all-in-one image embeds
Postgres and Redis under `/jadawel/data`, which on a host with no persistent
volume means the database is destroyed on every redeploy.

**Pushing code does not change what is deployed.** Publish first, then redeploy.

## 1. Publish an image

Actions → **Publish all-in-one image** → Run workflow, on `main`, with a tag such as `2.2.2`. Expect 30–60
minutes cold. It pushes `ghcr.io/azizahmed/jadawel_cranl:<tag>` and `:latest`.

Then decide the package's visibility, at
`github.com/users/Azizahmed/packages/container/jadawel_cranl/settings`:

- **Public** — CranL pulls with no credentials. The repository stays private,
  but the built application (including the fork's frontend bundle) becomes
  publicly downloadable.
- **Private** — requires CranL to hold a GHCR pull credential. If the wizard has
  no registry-credentials field, this option does not work and the image must be
  public.

Pin the published tag in the root `Dockerfile` (`ARG JADAWEL_IMAGE=...`) and
commit. Leaving it at `latest` means a redeploy silently picks up whatever was
published most recently.

## 2. Create the managed backing services

New → Database, twice: **Postgres** and **Redis**. Note each connection string.
Both are mandatory — `prod-lite` contains no database or cache of its own, and
the container filesystem does not survive a redeploy.

Uploaded files need S3 for the same reason; without `AWS_*` set they are written
to `/jadawel/data/media` and vanish on the next deploy.

## 3. Create the app

New app, and because these cannot be changed afterwards, get them right first
time:

| Setting | Value |
|---|---|
| Repository | `Azizahmed/jadawel_cranl` |
| Branch | `main` |
| Build Type | **Dockerfile** |
| Port | **80** — the image serves through its bundled Caddy, not 3000 |

The Dockerfile must be named `Dockerfile` and sit at the repository root, which
is where this repo now keeps it, regardless of what the wizard's path field
suggests.

## 4. Environment variables

```bash
for n in SECRET_KEY JADAWEL_JWT_SIGNING_KEY; do echo "$n=$(tr -dc 'a-z0-9' </dev/urandom | head -c50)"; done
```

The list below was written before the first deploy and proved incomplete. Five
more variables turned out to be mandatory — `PORT=3000` above all, without which
the container crash-loops. See [cranl_fix.md](../cranl_fix.md) for the full
working set and why each is needed.

| Variable | Value | Why |
|---|---|---|
| `PORT` | `3000` | CranL injects `PORT=80` to match the routing port, and Nitro obeys it — so the web-frontend tries to bind Caddy's socket and dies with `EADDRINUSE :::80`. `NITRO_PORT` does not override it. |
| `DISABLE_VOLUME_CHECK` | `yes` | Boot otherwise stops at the unmounted-data-folder warning. Safe: Postgres and Redis are external. |
| `JADAWEL_RUN_MINIMAL` | `yes` | Folds the export worker into the main worker on a 4 GB plan. |
| `JADAWEL_AMOUNT_OF_WORKERS` | `1` | Required for the above to take effect. |
| `NITRO_CLUSTER_WORKERS` | `2` | Uses both bounded SSR workers validated by the production load gate. The root Dockerfile also sets this value; keep it explicit if the app is recreated from another deployment file. |
| `SYNC_TEMPLATES_ON_STARTUP` | `false` | Drops a step that can take 30 minutes from every boot. |
| `JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION` | `false` | The fork reconciles its six authoritative local templates synchronously after migrations. Leave core's broad 150+ template sync disabled; `ArabaseConfig` also enforces this setting in-process. |
| `SECRET_KEY` | *generated* | Must be set explicitly. `jadawel.sh` otherwise generates one into `/jadawel/data/.secret`, which is ephemeral here — so every redeploy would invalidate all sessions. |
| `JADAWEL_JWT_SIGNING_KEY` | *generated* | Same, via `.jwt_signing_key`. Regenerating it logs everyone out. |
| `JADAWEL_PUBLIC_URL` | `https://jadawl.site` | Must exactly match the browser URL, scheme included, no trailing slash. |
| `DATABASE_URL` | *from managed Postgres* | Or the `DATABASE_HOST` / `PORT` / `NAME` / `USER` / `PASSWORD` set. |
| `REDIS_URL` | *from managed Redis* | Or the `REDIS_HOST` / `PORT` / `PASSWORD` set. |
| `JADAWEL_MCP_PROTECTION_REDIS_URL` | *from a dedicated managed Redis* | Required before enabling MCP protected fields. Do not reuse `REDIS_URL` in production. |
| `JADAWEL_MCP_PROTECTION_FINGERPRINT_KEYS` | *generated JSON keyring* | Private base64-encoded 32-byte HMAC keys; retain the previous key for at least 24 hours during rotation. |
| `JADAWEL_MCP_PROTECTION_ACTIVE_KEY_ID` | *current key ID* | Must name one entry in the fingerprint keyring. |
| `FEATURE_FLAGS` | `mcp-protected-fields` | Enables admission of non-empty endpoint protection policies after the dedicated Redis and fingerprint-key settings above are ready. Without it, enforcement remains fail-closed and policy writes are rejected. |
| `DISABLE_EMBEDDED_PSQL` | `yes` | **Required on the lite image.** Without it the startup script runs `chown -R postgres:postgres` for a user that only exists in the full image, and a missing database silently becomes a confusing failure instead of a loud one. |
| `DISABLE_EMBEDDED_REDIS` | `yes` | Same, for `chown -R redis:redis`. |
| `AWS_ACCESS_KEY_ID` | | Uploads are lost on redeploy without S3. |
| `AWS_SECRET_ACCESS_KEY` | | |
| `AWS_STORAGE_BUCKET_NAME` | | |
| `AWS_S3_REGION_NAME` | | |
| `AWS_S3_ENDPOINT_URL` | | Only for non-AWS S3. |

Leave `JADAWEL_CADDY_ADDRESSES` unset. Its `:80` default is correct — CranL owns
TLS, and pointing Caddy at an `https://` address makes it try to obtain its own
certificate on a port it cannot reach, which hangs the deploy.

Optional SMTP (password resets and invitations do not work without it) — same
variables as [DEPLOYMENT.md §3](DEPLOYMENT.md).

## 5. Deploy and create the first account

Migrations run automatically on startup. Watch the log until the backend reports
it is listening, then open the domain and **sign up through the web form**. The
first account created becomes staff.

Do not use `createsuperuser` for it: the `show_admin_signup_page` flag is only
cleared by the signup API, so a CLI-made account leaves it set and `/login`
redirects to `/signup` permanently, with no way in through the UI.

## Updating

1. Push code.
2. Run the publish workflow to build a new image tag.
3. Bump `ARG JADAWEL_IMAGE` in the root `Dockerfile` and commit.
4. Redeploy on CranL.

Skipping step 2 or 3 redeploys the same image.

## MCP protection load canary

After provisioning the dedicated protection Redis, run the release canary from
an application container that can resolve its private Redis hostname:

```bash
docker exec jadawel_cranl-backend-1 sh -lc \
  'cd /jadawel/backend/src/jadawel && /jadawel/venv/bin/python manage.py mcp_protection_load --yes'
```

The command uses synthetic values, creates and removes its digest-only test
reservations, and prints only aggregate counts, memory, latency, and admission
results. It proves the 50,000-token global boundary, five-endpoint distribution,
cross-worker redemption, six-issuer/250 ms contention gate, and recovery after a
worker dies while holding an issuer lease against the actual Redis configuration.
Run it only against the isolated protection vault;
it deliberately removes keys under the MCP protection namespace during cleanup.

The Redis-interruption mutation rollback and production observability canaries
still require an operational drill with the deployment's normal database and
logging capture. Do not interrupt the live service to manufacture that evidence.

## Troubleshooting

**`Railpack could not determine how to build the app`** — the app was created
with the Railpack build type. It cannot be changed; recreate the app with
Dockerfile.

**Build OOMs or is killed with no error** — something is building the repo from
source rather than pulling the published image. Check that the root `Dockerfile`
is the one being used and that `ARG JADAWEL_IMAGE` points at a tag that exists.

**`denied` / `unauthorized` pulling from ghcr.io** — the GHCR package is private
and CranL has no credential for it. See §1.

**Container starts, then exits during startup with a `chown` error** —
`DISABLE_EMBEDDED_PSQL` / `DISABLE_EMBEDDED_REDIS` are not set. See §4.

**Everyone is logged out after each deploy** — `SECRET_KEY` or
`JADAWEL_JWT_SIGNING_KEY` is unset and being regenerated. See §4.

**UI loads but the grid stays empty and websockets fail** —
`JADAWEL_PUBLIC_URL` does not exactly match the browser URL.

**The template picker is empty or shows the upstream catalog** — startup did not
finish the fork's local catalog reconciliation. Read the migration/container log;
a successful startup records `Local template catalog is ready after migrations`
and exposes exactly six templates in two categories. Do not enable the broad core
template sync.

**`/api/*` returns a Nuxt 404 page instead of JSON** — the host being requested
is not named in `JADAWEL_PUBLIC_URL`, so `Caddyfile:82-131` routes backend paths
to the frontend. Add the extra host to `JADAWEL_EXTRA_PUBLIC_URLS`.

**Saving an MCP protection policy shows a network error or a CORS failure** —
confirm the running image allows `Idempotency-Key` in
`Access-Control-Allow-Headers`, and set `FEATURE_FLAGS=mcp-protected-fields`
before redeploying. A CranL environment save alone does not recreate the running
container.

**Uploaded files disappear after a deploy** — no S3 configured. See §4.
