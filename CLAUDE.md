@AGENTS.md

## Fork identity

This repo is **Jadawel** — an Arabic-first, RTL fork of Baserow. AGENTS.md above
is unmodified upstream Baserow guidance: accurate for build/test/lint, but silent
on deploy and fork scope, both covered below.

## Remotes and branches

Two remotes point to two different repos — the wrong one silently diverges work
with no path back:

- `origin` (`Azizahmed/Jadawel`) — the real dev repo. All feature commits belong
  here.
- `cranl` (`Azizahmed/jadawel_cranl`) — the deploy mirror, carrying an extra root
  `Dockerfile` and publish workflow. Never commit feature work directly to it;
  fast-forward its `main` from the `origin` branch being released, then publish
  an image.

## Deploying

**CranL is the only deploy target.** It serves `jadawl.site` from a prebuilt
image: the monorepo cannot be built there (no Compose pack, Railpack finds no
manifest, 4 GB RAM ceiling), so GitHub Actions builds it and CranL only pulls
the result. Procedure in `docs/DEPLOY_CRANL.md`.

Every push to `main` redeploys production: CranL rebuilds the root `Dockerfile`
on each push. That file pins an image by digest, so new application code ships
only through: push → run *Publish all-in-one image* → bump `ARG JADAWEL_IMAGE`
→ push again. The pin commit deploys itself. Any other push to `main` restarts
production on the same image, so don't push there casually. Environment changes
made in the CranL dashboard still need a manual Redeploy.

### Coolify is decommissioned

`jadawel.azoz.cloud` is switched off and is not coming back. Treat every
mention of it as history:

- `docs/DEPLOYMENT.md` describes that setup and no longer applies to anything
  running. Kept because the Traefik/compose detail is the reference if the fork
  is ever self-hosted again.
- `codex/hostinger-coolify-deploy` is no longer the production branch and is far
  behind. Do not merge into it expecting a release — nothing watches it now.
- `docker-compose.yml`'s Coolify/Traefik wiring is unused by CranL, which
  terminates TLS itself and routes straight to the container.

## Fork-specific docs

`docs/` holds plans and audits specific to this fork (RTL/i18n completion,
dashboard widgets, Arabic glossary, production hardening, audits) — check there
before re-deriving scope or history that's already written down.

`website/index.html` and `website/landing.html` are marketing pages, not part
of the deployed app image; they need separate hosting to go live.

## Skills

`.claude/skills` is a symlink to `.agents/skills`, the canonical location for project skills. Both paths resolve to the same directory.

## Agent skills

### Issue tracker

Issues and specs are tracked in GitHub Issues for `Azizahmed/jadawel_cranl`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage labels defined for this repository. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain layout. See `docs/agents/domain.md`.
