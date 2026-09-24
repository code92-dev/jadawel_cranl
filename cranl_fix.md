# CranL deployment — what broke, why, and how to fix it again

Reference for the CranL deployment of Jadawel, written after getting it from
"nothing works" to a running app on 2026-08-02. Read
[docs/DEPLOY_CRANL.md](docs/DEPLOY_CRANL.md) for the procedure; this file is the
diagnostic history and the runbook for when it breaks.

Live at **https://jadawel-img0kf.cranl.net** (custom domain `jadawl.site`
pending DNS).

---

## The shape of it

CranL cannot build this repository. It offers Railpack (auto-detect) and
Dockerfile as build types — no Docker Compose — and its Pro plan gives 4 GB per
app, while the Nuxt production build peaks above that. So the build happens on a
GitHub runner and CranL only pulls the result:

```
Azizahmed/Jadawel  (source of truth — dev repo)
   │  copied to
   ▼
Azizahmed/jadawel_cranl @ main   ← deployment repo, this one
   │  .github/workflows/publish-image.yml, on a 16 GB runner
   ▼
ghcr.io/azizahmed/jadawel_cranl:2.2.2   (public package, 437 MB, 19 layers)
   │  root Dockerfile: FROM that tag
   ▼
CranL app "jadawel"  →  Bunny CDN edge  →  container :80 (Caddy)
                                              ├── web-frontend :3000
                                              └── backend :8000
   external: jadawel-postgres, jadawel-redis, jadawel-media (all Riyadh / Saudi-4)
```

**Pushing code does not change what is deployed.** Publish a new image first.

The image is the `prod-lite` target — no embedded Postgres or Redis, because
CranL apps have no persistent volume and an embedded database would be destroyed
on every redeploy.

---

## The five failures, in the order they happened

### 1. `Railpack could not determine how to build the app`

Railpack looks for an application manifest at the repository root. This is a
monorepo whose manifests live in `backend/` and `web-frontend/`, so detection
failed before any build step.

**Fix:** build type **Dockerfile**, with a `Dockerfile` at the repository root.
It must be named exactly that and sit at the root regardless of what the
wizard's path field suggests.

**Note:** build type and branch can only be set at app creation — Settings
exposes only domain, port and delete, and there is no update-application API. A
wrong build type means deleting the app and recreating it.

### 2. `401 Unauthorized` pulling from ghcr.io

The GHCR package was private. CranL has nowhere to store a registry
credential — not in the create wizard, not in Settings.

**Fix:** make the *package* public. This is separate from repository visibility;
a package only inherits it at creation. The toggle lives at
`github.com/users/Azizahmed/packages/container/jadawel_cranl/settings` →
Danger Zone, **not** in the repository's settings.

Verify from anywhere, no credentials needed:

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:azizahmed/jadawel_cranl:pull&service=ghcr.io" | jq -r .token)
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  https://ghcr.io/v2/azizahmed/jadawel_cranl/manifests/2.2.2
# 200 = CranL can pull it. 401 = package is still private.
```

Checked before publishing: no credentials ship in the image (the only
secret-shaped files are `deploy/*/.env.testing`, whose every value is the
literal string `jadawel`), and there is no license obstacle — this fork has zero
files under `premium/` or `enterprise/`, so it is MIT plus CC-BY-SA docs.

### 3. The log showed one line and stopped

The container log contained only Jadawel's warning about running without a
mounted data folder, hiding everything after it.

**Fix:** `DISABLE_VOLUME_CHECK=yes`. Safe here because Postgres and Redis are
external; only media and Caddy state live in `/jadawel/data`, and media belongs
in S3 anyway.

### 4. The real cause — `EADDRINUSE: address already in use :::80`

With the boot unblocked, the actual failure appeared: the Nuxt web-frontend
crash-looping on port 80, retrying four times, reaching supervisor `FATAL`, at
which point Jadawel's watcher declared a crash and shut down the whole
container.

**Why:** Caddy owns `:80` inside the all-in-one image; the frontend belongs on
3000. CranL injects `PORT=80` into the container to match the app's routing
port, and Nitro reads `PORT` to decide where to listen — so the frontend kept
trying to take Caddy's socket.

**Current fix:** the root deployment `Dockerfile` adds
`environment=PORT="3000"` only to Supervisor's web-frontend program. CranL now
filters attempts to persist a user-defined `PORT`, so the old dashboard
workaround below no longer survives an environment refresh. `NITRO_PORT=3000`
and `JADAWEL_WEB_FRONTEND_PORT=3000` alone do **not** win because Nitro gives
`PORT` precedence.

Historically, setting `PORT=3000` explicitly in the dashboard worked because a
runtime app variable beat CranL's injected `PORT=80`. The Supervisor override
is stronger and scoped: Nitro receives 3000, while Caddy still owns `:80`.

This is the failure most likely to recur, because it comes back the moment
`PORT` is cleared or the app is recreated.

**How it presents:** every path returns HTTP 502 from BunnyCDN in well under a
second. A fast 502 on `/`, `/api/settings/` and `/_health/` alike means nothing
is bound to :80 in the container — Caddy up but backends down would give slower,
path-dependent responses instead.

### 5. Container cycled a few times during first-boot migrations

Expected, not a fault. Django migrations resume where they left off, so the
restarts worked through them and it came up clean.

### 6. Historical: all 157 templates missing from the template picker

> Superseded by release 2.9.2. The fork now treats six bundled Arabic/English
> templates as an authoritative local-only catalog, disables core's broad sync,
> and reconciles synchronously after migrations. The notes below explain the old
> production failure but are no longer the operating procedure.

Found after the deploy was otherwise healthy. Nothing was lost: the templates
ship inside the image as `backend/templates/*.json` and had simply never been
imported into the fresh managed Postgres.

Cause was `SYNC_TEMPLATES_ON_STARTUP=false`, set in §4's env table to avoid a
30-minute boot stall. `backend/docker/docker-entrypoint.sh:30`:

```bash
JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION=${JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION:-$SYNC_TEMPLATES_ON_STARTUP}
```

The trigger variable *defaults to* the startup variable, so switching off the
blocking boot-time sync silently switched off the non-blocking post-migration
one too. The two are separable, and want opposite values here:

| Variable | Value | Effect |
|---|---|---|
| `SYNC_TEMPLATES_ON_STARTUP` | `false` | Boot does **not** wait for the sync |
| `JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION` | `false` | Broad core sync is disabled; the fork reconciles its local catalog during migration startup |

Fix was to set the trigger to `true` and Reload. The task routes to the `export`
queue (`backend/src/jadawel/core/tasks.py:23`), which under `JADAWEL_RUN_MINIMAL`
is served by the combined worker (`docker-entrypoint.sh:373-393`) — so it is
picked up rather than sitting unrouted. It took **13m15s** for 157 templates
while the app kept serving traffic normally.

156 of 157 imported. `event-staffing` failed and was skipped without aborting the
rest, which is the fork's patch to `CoreHandler.sync_templates` working as
designed (`PATCHES.md`, `backend/src/jadawel/core/handler.py:1880-1940`).

The `view type 'kanban'/'calendar'/'timeline' is not available on this instance`
warnings during the sync are expected and not CranL-specific: those view types
are premium/enterprise, which this fork removes. Templates import with those
views dropped.

Release 2.9.2 replaces this queue-based workaround. Leave
`JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION=false`; a successful migration
now means the six-template local catalog is ready, and normal restarts use the
fast idempotent state check.

### 7. `/api/*` returns a Nuxt 404 on the `cranl.net` hostname

Not a fault either, but it looks exactly like a broken backend. The `Caddyfile`
gates the backend routes on the request host, lines 82-89:

```caddy
@is_jadawel_tool {
    expression `
        "{$JADAWEL_PUBLIC_URL}".contains({http.request.host}) ||
        "{$JADAWEL_EXTRA_PUBLIC_URLS}".split(",")
            .filter(u, u != "" && u.contains({http.request.host}))
            .size() > 0
    `
}
```

`/api/*`, `/ws/*`, `/mcp/*`, `/assistant/*` and `/static/*` are proxied to Django
**only** inside that matcher (line 118-131). Any other host falls through to the
catch-all `reverse_proxy localhost:3000` on line 133, so API calls are answered
by Nuxt with its own 404 page — a JSON body containing
`"message": "لم يتم العثور على الموقع"`, which is the giveaway that the request
never reached Django.

With `JADAWEL_PUBLIC_URL=https://jadawl.site/`, `jadawl.site` works completely
and `jadawel-img0kf.cranl.net` 404s on every path. To keep both hosts alive, set
`JADAWEL_EXTRA_PUBLIC_URLS` to the comma-separated others — do not try to put two
URLs in `JADAWEL_PUBLIC_URL`.

---

## Working environment variables

| Variable | Value | Why |
|---|---|---|
| `PORT` | **Do not add in CranL** | The root deployment `Dockerfile` now scopes `PORT=3000` to the web-frontend process because CranL filters the reserved key. Without that image-layer override, Nuxt fights Caddy for `:80` (§4). |
| `POSTHOG_PROJECT_API_KEY`, `POSTHOG_HOST` | **Do not add in CranL** | Analytics is intentionally disabled. CranL retained the deleted values in running containers, so the root deployment `Dockerfile` also forces the legacy and Nuxt runtime names empty for every Supervisor child process. |
| `DISABLE_VOLUME_CHECK` | `yes` | Unblocks boot; no persistent volume by design (§3). |
| `SECRET_KEY` | *50 chars, generated* | Must be explicit — `jadawel.sh:201` otherwise writes one to the ephemeral `/jadawel/data/.secret`, so every redeploy would invalidate all sessions. |
| `JADAWEL_JWT_SIGNING_KEY` | *50 chars, generated* | Same, via `.jwt_signing_key`. |
| `JADAWEL_PUBLIC_URL` | current domain, no trailing slash | Jadawel rejects requests on any host that does not match. Must be switched when the domain changes. |
| `DATABASE_URL` | internal, from `jadawel-postgres` | |
| `REDIS_URL` | internal, from `jadawel-redis` | Celery and websockets do not work without Redis; no BaaS replaces it. |
| `JADAWEL_MCP_PROTECTION_REDIS_URL` | *leave unset* | Optional. Unset, mask tokens are kept in the app's PostgreSQL, which needs no extra service. Set it only for a dedicated Redis vault; shared Redis is forbidden in production. |
| `JADAWEL_MCP_PROTECTION_FINGERPRINT_KEYS` | *optional* private JSON keyring | Unset, a dedicated key is derived from `SECRET_KEY`. Set base64-encoded 32-byte HMAC keys only to rotate independently of it. Never copy this value into frontend configuration or logs. |
| `JADAWEL_MCP_PROTECTION_ACTIVE_KEY_ID` | *with the keyring only* | Must select a configured fingerprint key. |
| `FEATURE_FLAGS` | `mcp-protected-fields` (harmless, no longer needed) | Field protection is on by default from the database-vault image. `mcp-protected-fields-staff` on its own restricts it to staff. Creating or extending a protection policy is refused while `/api/arabase/mcp/protection/readiness/` is not ready. |
| `DISABLE_EMBEDDED_PSQL` | `yes` | Required on the lite image — the startup script otherwise runs `chown -R postgres:postgres` for a user that exists only in the full image. |
| `DISABLE_EMBEDDED_REDIS` | `yes` | Same, for `chown -R redis:redis`. |
| `JADAWEL_RUN_MINIMAL` | `yes` | Folds the export worker into the main worker (`backend/docker/docker-entrypoint.sh:373-393`). |
| `JADAWEL_AMOUNT_OF_WORKERS` | `1` | Required for the above to take effect. |
| `NITRO_CLUSTER_WORKERS` | `2` | Runs the bounded two-worker SSR cluster validated at 600 requests and concurrency 60; the root Dockerfile supplies the same value. |
| `SYNC_TEMPLATES_ON_STARTUP` | `false` | Removes a step that can take 30 minutes from every boot. |
| `JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION` | `false` | Keep the broad upstream sync disabled. The fork enforces and reconciles its six local templates synchronously after migrations (§6). |

Leave `JADAWEL_CADDY_ADDRESSES` unset. Its `:80` default is correct — CranL owns
TLS, and pointing Caddy at an `https://` address makes it try to obtain its own
certificate on a port it cannot reach, which hangs the deploy.

### Not yet set, and should be

| Variable | Why |
|---|---|
| `JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=yes` | TLS terminates at CranL's proxy, so Django cannot currently tell requests arrived over HTTPS. Also passes `--forwarded-allow-ips='*'` to gunicorn so real client IPs are visible. See `docs/PRODUCTION_HARDENING.md` §2.3. |
| MCP protection vault on images up to 2.3.9 | Those images keep mask tokens only in Redis and fail every protected read closed without the three `JADAWEL_MCP_PROTECTION_*` values. From the database-vault image on, nothing needs setting. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL` | **Uploaded files are lost on every redeploy until these exist.** Blocked on a CranL bug: creating a bucket token returns "Quota limit exceeded. You can create no more than 50 tokens". Any S3-compatible provider works as a fallback, at the cost of files leaving Saudi Arabia. |

---

## App settings that cannot be changed later

| Setting | Value |
|---|---|
| Repository | `Azizahmed/jadawel_cranl` |
| Branch | `main` |
| Build path | `/` |
| Build type | Dockerfile, path `Dockerfile` |
| Port | **80** — the image serves through its bundled Caddy |

---

## Runbook

### Deploying a code change

1. Merge the change into `Azizahmed/jadawel_cranl` `main`. Feature work belongs
   in `Azizahmed/Jadawel`; this repo is a deployment copy, and committing
   directly here diverges the two trees.
2. Actions → **Publish all-in-one image** → Run workflow, with a new tag.
   Roughly 10 minutes.
3. Bump `ARG JADAWEL_IMAGE` in the root `Dockerfile` to that tag and commit.
   Leaving it at `latest` means a redeploy silently picks up whatever was
   published last.
4. Redeploy on CranL.

Skipping 2 or 3 redeploys the identical image.

### Changing only environment variables

Actions → **Reload**. It picks up env changes without a rebuild.

Note: **Deploy** returned "USA region is temporarily unavailable for new
deployments" on 2026-08-02, which is why Reload was used. Worth re-running a
real deploy once that clears.

### Moving to `jadawl.site` — done, 2026-08-03

`https://jadawl.site` is the live URL and resolves, serves valid TLS and reaches
Django. `https://jadawel-img0kf.cranl.net` now 404s on every path, by design: see
§7 — the Caddyfile only proxies backend routes for hosts named in
`JADAWEL_PUBLIC_URL`. Add it to `JADAWEL_EXTRA_PUBLIC_URLS` if a working fallback
host is wanted.

Kept for the next domain change:

1. Point the DNS at `jadawel-img0kf.cranl.net`. An apex `CNAME` is invalid DNS —
   use the provider's `ALIAS`/`ANAME`, or Cloudflare's CNAME flattening. On
   Cloudflare keep the record **DNS-only (grey cloud)** until the certificate
   issues, or the proxy intercepts the ACME challenge.
2. Once SSL is active, set `JADAWEL_PUBLIC_URL` to the new origin and Reload.
   Jadawel rejects requests on any host that does not match it, so the two must
   change together, and the old host stops working the moment it is dropped.

The value in place is `https://jadawl.site/`, **with** a trailing slash, contrary
to the advice everywhere else in these docs. It happens to work because §7's
check is a substring match and the CORS header on line 20 of the `Caddyfile`
tolerates it, but it is worth trimming next time the variable is touched.

---

## Troubleshooting by symptom

| Symptom | Cause | Fix |
|---|---|---|
| Fast 502 from BunnyCDN on every path | Nothing bound to :80 — container crashed or crash-looping | Read the container log. Most likely the Supervisor frontend `PORT` override is missing (§4). |
| `EADDRINUSE :::80` in the log | Nuxt taking Caddy's port | Confirm the root deployment `Dockerfile` adds `environment=PORT="3000"` to the web-frontend program. |
| Log stops after the data-folder warning | Volume check blocking boot | `DISABLE_VOLUME_CHECK=yes` |
| `chown` / "no such user" at startup | Embedded services not disabled on the lite image | `DISABLE_EMBEDDED_PSQL=yes`, `DISABLE_EMBEDDED_REDIS=yes` |
| `401 Unauthorized` pulling the image | GHCR package private | Make the package (not the repo) public |
| `Railpack could not determine how to build the app` | Wrong build type; cannot be changed | Recreate the app with Dockerfile |
| Container restarts repeatedly on first boot | Migrations in progress | Expected; they resume and finish |
| Killed / exit 137 | OOM on the 4 GB plan | `JADAWEL_RUN_MINIMAL=yes`, `JADAWEL_AMOUNT_OF_WORKERS=1`, `SYNC_TEMPLATES_ON_STARTUP=false` |
| UI loads, grid empty, websockets fail | `JADAWEL_PUBLIC_URL` does not match the browser URL | Correct it and Reload |
| Template picker empty or shows 157 templates | Local catalog reconciliation did not complete | Keep both template-sync variables `false`, redeploy, and require the migration log to report `Local template catalog is ready after migrations` (§6) |
| `/api/*` returns JSON with `"message": "لم يتم العثور على الموقع"` | Request host is not in `JADAWEL_PUBLIC_URL`, so Caddy sent it to Nuxt instead of Django | Add the host to `JADAWEL_EXTRA_PUBLIC_URLS` (§7) |
| Uploaded files vanish after a deploy | No S3 configured | Set the `AWS_*` variables |
| Everyone logged out after a deploy | `SECRET_KEY` / `JADAWEL_JWT_SIGNING_KEY` being regenerated | Set both explicitly |
| `/api/schema.json` returns a Django 500 | Pre-existing upstream schema-generation bug (see open items) — **not** a sign of a bad deploy | Ignore; use another endpoint to check liveness |

---

## Open items

1. **Login rate limiting is gone.** It was implemented as Traefik middleware in
   `docker-compose.yml` (`docs/PRODUCTION_HARDENING.md` §1.5) — 5 req/s per IP on
   `/api/user/token-auth/` and the reset-password endpoints. CranL never reads
   that file, so credential stuffing is currently limited only by network speed.
   Jadawel's own throttle cannot substitute: it limits concurrency per user, not
   attempts per IP. Check whether CranL's CDN tab offers rate limiting or a WAF.
2. **Public signup.** Anyone who finds the URL can register. Disable it in the
   admin panel once the first staff account exists
   (`docs/PRODUCTION_HARDENING.md` §2.1, its highest-priority item).
3. **S3 credentials** — blocked on the CranL token quota bug.
4. **`jadawl.site`** — DNS and SSL pending.
5. **`JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER`** — not set.
6. **Resolved: `PORT=3000` is scoped in Supervisor.** CranL filters the reserved
   environment key, so the root deployment `Dockerfile` injects it only into
   the frontend program and fails its build if the inherited command changes.
7. **`/api/schema.json` returns 500**, so `/api/redoc/` renders nothing. It
   predates the fork's own code: `manage.py spectacular` fails identically at
   `5f6b4cf55` and at the chart-widget commit, in drf-spectacular's
   `_insert_field_validators` — it calls `.get()` on the `additionalProperties`
   schema of a `DictField`, which resolved to `None`. Cosmetic for the running
   app (nothing but the docs endpoint uses it), but it does mean the API schema
   cannot be used to check what a deploy is running.

## Facts worth not re-deriving

- The first account created through the **signup form** becomes staff. Do not
  use `createsuperuser` for it: `show_admin_signup_page` is only cleared by the
  signup API, so a CLI-made account leaves it set and `/login` then redirects to
  `/signup` permanently, with no way in through the UI.
- pgvector is optional — `is_pgvector_enabled()` in
  `backend/src/jadawel/core/pgvector.py` feature-detects it, and its absence
  just disables embedding fields.
- Supabase would work as the database (it is Postgres) but adds nothing over
  `jadawel-postgres`, and its PostgREST auto-exposes the `public` schema, where
  Jadawel creates every user table without RLS. Convex cannot host this app at
  all — Jadawel issues live DDL against Postgres and has no SQL-free mode.
- CI and Dependabot are deliberately disabled in this repository; it re-tests
  nothing and merges nothing.
- Image published 2026-08-02 by run 30758451992, digest
  `sha256:9bd2a24b2bf1a7ba98d7010481cb91c1698acde367095c5f2a0ad54a0bdb6238`.
