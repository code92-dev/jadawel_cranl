# Security Brief — Jadawel

**Date:** 2026-09-30 · **Scope:** whole repo + passive checks on app.jadawl.site and jadawl.site
**Profile:** Standard · **Live header grades:** app.jadawl.site **A (90/100)** · jadawl.site (marketing) B (83/100)

## The 2-minute read

The audit scanned the entire codebase (secrets in all git history, dependency
vulnerabilities, static analysis, Docker/CI configuration) and passively probed
the live site. **No leaked secrets, no injected code, and no broken access
control were found.** The real risks were ordinary and fixable: outdated
libraries and a few missing response headers.

### What was fixed (code changes, in this working tree)

| Risk | Severity | What was done |
|---|---|---|
| PyJWT — the library that signs every login session — had 1 critical + 5 high CVEs | High | Upgraded to 2.15.1; all auth tests pass |
| anyio (critical CVE) and httpx2/httpcore2 (high) | High/Med | Upgraded; integration tests pass |
| A crafted backup file could theoretically write files outside its extraction folder during a restore | Low | Extraction hardened; all 80 backup tests pass |
| No `Cross-Origin-Opener-Policy` header | Low | Added to the reverse-proxy configs |
| No `security.txt` (how researchers report vulnerabilities) | Low | Added |

### What needs you (not fixable from code alone)

1. **The marketing domain jadawl.site does not send HSTS or Permissions-Policy**
   (the application domain app.jadawl.site already passes — grade A). The
   headers are lost at the Bunny layer in front of the marketing site.
   - Set `JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=yes` in the CranL environment
     (this also enables Secure cookies), then purge the Bunny cache.
   - If they still don't appear, add two Edge Rules in the Bunny dashboard for
     the marketing pull zone (exact values in the Fix Plan).
2. **Deploy the fixes**: run the *Publish all-in-one image* workflow and bump
   the pin in the root `Dockerfile` — pushing code alone never deploys. After
   the deploy, the app also gains the COOP header, security.txt and a Secure
   locale cookie.

### Risks we deliberately left for later (low)

- Old vulnerable packages in dev-only tooling (test runner, Zapier template,
  email compiler) — these never ship to production; refresh when convenient.
- CI actions pinned to version tags instead of commit SHAs — pin them when
  touching the workflows.
- The support widget on the marketing site posts messages with a wildcard
  target — worth tightening on the next touch.
- The real-time WebSocket connects with the JWT in the URL query string
  (`?jwt_token=…`, an upstream Baserow pattern) — tokens are short-lived, but
  the server/CDN shouldn't log `/ws/` query strings, and a proper WS ticket
  mechanism is worth planning in core (Fix Plan §15).

### Checked and found in good shape

Full git history is clean of real secrets (all 35 scanner hits are dummy test
values). No SQL injection sinks in the fork's code. Django's defaults are
locked down (debug off, host allowlist, env-only secrets). The Page-view
feature sandboxes untrusted AI-authored HTML properly, media files get a strict
sandbox CSP, and the production image is pinned by digest.

## What to do next

| When | Action |
|---|---|
| This week | Set the CranL env var, publish + deploy, purge Bunny cache, verify headers (Fix Plan §6-7) |
| On every PR going forward | Run the two fork gates as usual; consider adding Gitleaks + Semgrep to CI (templates available) |
| Monthly | Re-run the dependency scan (`trivy fs`) |
| Yearly | Refresh the `Expires` date in security.txt; consider an external pentest before any big public launch |

**Files:** detailed tasks in `security-reports/SECURITY_FIX_PLAN.md` · machine-readable results in `security-reports/findings.json` · raw scanner output in `security-reports/raw/` (git-ignored).
