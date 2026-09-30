# Security Fix Plan — Jadawel (jadawel_cranl)

Generated 2026-09-30 from commit `8318a765`. Standard assurance profile: code
scans (Gitleaks, Semgrep, Trivy), passive live checks on jadawl.site, and manual
review. Raw scanner output is in `security-reports/raw/` (git-ignored).

Tasks are ordered. IDs match `security-reports/findings.json`.

---

## Done in this session (verify after deploy)

### 1. SEC-DEP-001/002/003 — Backend runtime dependency bumps (uv.lock)

- `cd backend && uv lock --upgrade-package pyjwt --upgrade-package anyio --upgrade-package httpx2 --upgrade-package httpcore2`
- Result: pyjwt 2.13.0→**2.15.1** (CVE-2026-102268 CRITICAL + 5 HIGH), anyio
  4.12.1→**4.15.1** (CVE-2026-63374 CRITICAL), httpx2/httpcore2 2.3.0→**2.13.1**.
- Verified locally: JWT/auth tests, core HTTP request service tests (22 passed),
  backup tests (80 passed).
- **These changes only ship when the _Publish all-in-one image_ workflow runs and
  the root `Dockerfile` pin is bumped — code pushes do not deploy.**

Acceptance:
- [ ] `git diff backend/uv.lock` contains the four upgrades
- [ ] `DATABASE_URL=postgres://jadawel:jadawel@localhost:55432/jadawel just b test` green
- [ ] After publish+deploy: `docker run --rm -v "$PWD:/src" aquasec/trivy fs backend/uv.lock` shows no CRITICAL

### 2. SEC-SAST-001 — tarfile extraction hardened

- `backend/src/jadawel/core/management/backup/backup_runner.py`:
  `extractall(temporary_directory_name, filter="data")` — rejects absolute
  paths, `..` traversal, symlinks and device nodes in a (possibly crafted)
  backup archive. Logged in `PATCHES.md`.
- Acceptance: `pytest tests/arabase/test_backup.py tests/arabase/test_backup_admin.py -q` → 80 passed ✅ (already run)

### 3. SEC-HDR-003 — Cross-Origin-Opener-Policy added

- `Caddyfile` baseline header block: `Cross-Origin-Opener-Policy "same-origin-allow-popups"`
  (allow-popups keeps OAuth/SSO popups working). Parity in
  `deploy/nginx/no-caddy/nginx.conf`.
- `caddy validate` passes with `JADAWEL_CADDY_ADDRESSES=:8080`.
- Acceptance after redeploy: `curl -sI https://jadawl.site | grep -i opener-policy`

### 4. SEC-HDR-004 — security.txt (RFC 9116)

- `Caddyfile` now answers `/.well-known/security.txt` (Contact
  gotoaziz100@gmail.com, Expires 2027-09-30 — **refresh yearly**), nginx parity added.
- Acceptance after redeploy: `curl https://jadawl.site/.well-known/security.txt`

### 5. Repo hygiene

- `security-reports/raw/` added to `.gitignore` (scanner output can contain
  sensitive file locations).

---

## Requires the CranL/Bunny layer (user action)

### 6. SEC-HDR-001/002 — HSTS and Permissions-Policy missing on the **marketing domain** (jadawl.site)

Update after re-checking both live targets: **https://app.jadawl.site already
passes — grade A (90/100)** (raw report:
`security-reports/raw/jadawl-app-headers.json`). HSTS, Permissions-Policy,
CSP, XCTO, XFO and Referrer-Policy all arrive from the origin Caddy through
Bunny pull zone 6480768. The problem is confined to the **marketing pull zone
(6292730) in front of jadawl.site**, which strips even cache-MISS responses
of HSTS/Permissions-Policy while keeping platform-default headers.

Steps for the marketing zone:

1. Set `JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=yes` in the CranL environment
   (Secure cookies + Django HSTS; settings/base.py:1268-1287). Actions → Reload.
2. After redeploying the app, purge the Bunny cache and check
   `curl -sI https://jadawl.site | grep -iE 'strict-transport|permissions-policy'`.
3. If Bunny still strips them, add two Edge Rules on pull zone 6292730:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`

Acceptance: `check_headers.py https://jadawl.site` moves from **B (83/100)**
to A; `https://app.jadawl.site` stays A with COOP added after this branch
deploys (currently the only FAIL there).

App-domain leftovers (both already fixed in code, verify after deploy):

- COOP on frontend HTML responses — shipped in the Caddyfile (SEC-HDR-003).
- `i18n-language` cookie Secure flag — shipped in
  `web-frontend/config/nuxt.config.base.ts` (SEC-HDR-006).
- `/.well-known/security.txt` — shipped in the Caddyfile (SEC-HDR-004).

### 7. After deploy — re-verify everything

```bash
python3 scripts/check_headers.py https://jadawl.site   # (skill script) or:
curl -sI https://jadawl.site | grep -iE 'strict-transport|permissions|opener|security'
```

`security.txt` and the webmanifest/humans.txt MISSes from the B-grade report are
resolved by item 4; webmanifest/humans.txt are cosmetic/SEO and optional.

---

## Open recommendations (not fixed, ordered by value)

### 8. SEC-DEP-004 — refresh dev-only lockfiles (Low)

None of these ship in the production image; they are developer-machine risk only.

```bash
cd e2e-tests && yarn install && yarn upgrade axios playwright nanoid postcss && yarn install
cd ../integrations/zapier && yarn install && yarn upgrade form-data node-fetch semver lodash && yarn install   # form-data CVE-2025-7783 (CRITICAL)
cd ../../backend/email_compiler && yarn install && yarn upgrade && yarn install
```

### 9. SEC-DEP-005 — brace-expansion in web-frontend (Low, build-time ReDoS)

```bash
cd web-frontend && yarn up 'brace-expansion@^5.0.10' && yarn install && f test
```

### 10. SEC-CI-001 — pin GitHub Actions to commit SHAs (Low)

Replace `uses: <action>@vN` with the full commit SHA (keep a version comment):

- `actions/checkout@v4`, `actions/setup-node@v4`
- `astral-sh/setup-uv@v7`, `extractions/setup-just@v3`
- `docker/setup-buildx-action@v3`, `docker/build-push-action@v6`, `docker/login-action@v3`

### 11. SEC-IAC-001 — container hardening (Low)

- `deploy/all-in-one/Dockerfile`: pin base image by digest (pattern already
  used by the root Dockerfile), avoid bare `RUN apt update` without upgrade.
- Add `USER` where the base image permits. Most findings are inherited from
  upstream base images; the deployed image is already digest-pinned.

### 12. SEC-FE-001 — website/support.js message validation (Low)

- Pin outgoing `postMessage` target origin (currently `"*"`,
  website/support.js:1391) to the widget provider's origin.
- Add `event.origin` allowlist + payload shape checks to incoming handlers (~:937).

### 13. SEC-SAST-004 — share password policy (Low)

`backend/src/arabase/dashboard/share/handler.py:82`: enforce a minimum length
(suggest ≥ 8) before `share.set_password(password)`; add a backend test.
Guesses are already rate-limited via `JADAWEL_DASHBOARD_AUTH_RATE`.

### 14. SEC-FE-002 — lock down MarkdownIt intent (Info)

`web-frontend/modules/core/components/MarkdownIt.vue`: make
`new Markdown({ html: false })` explicit so enabling raw HTML later is a
deliberate, reviewed change. (The rich-text field path,
`parseMarkdown()` used by `GridViewFieldRichText.vue` and its variants, already
sets `{ html: false }` explicitly.)

### 15. SEC-FE-003 — JWT in the WebSocket query string (Medium — plan deliberately)

`web-frontend/modules/core/plugins/realTimeHandler.js:65` connects with
`new WebSocket(`${url}?jwt_token=${token}`)` — the short-lived access JWT rides
in the URL, where reverse-proxy/CDN access logs and `Referer` headers can
retain it. This is inherited from upstream Baserow's Django Channels design,
so the real fix is a core-file change (a WS auth ticket or `Sec-WebSocket-
Protocol` credential, validated in the ASGI middleware) and must go through
`PATCHES.md` per repo policy.

Interim mitigations (no code change):

- Keep the access-token lifetime short (bounds replay from any leaked log line).
- If the edge proxy logs full query strings for `/ws/`, stop doing that — in
  the Caddyfile the `log` directive can use `query` deletion, in Apache omit
  `%q` from the `LogFormat` for the WS vhost.

### 16. Gitleaks noise reduction (Info)

Add a `.gitleaksignore` with the fingerprints of the 35 false positives
(see `security-reports/raw/gitleaks.json` — all test fixtures, upstream's
committed test RSA key, and doc placeholders).

---

## Things checked and found solid (do not "fix")

- Django settings: `DEBUG` off by default, `ALLOWED_HOSTS` localhost-locked
  with explicit env additions, `SECRET_KEY` from env only, CSRF/secure-cookie
  flags gated behind a documented opt-in.
- Public dashboard/data-source isolation, share-token expiry, per-client rate
  limits, webhook outbound rules (no private addresses, https-only), Page-view
  iframe sandbox + `connect-src 'none'` CSP, media sandbox CSP, build-sourcemap
  404s, digest-pinned deploy image.
- No raw-SQL injection sinks in fork code (`backend/src/arabase/`).
- No live secrets in git history (all 35 gitleaks hits are dummies/fixtures).
