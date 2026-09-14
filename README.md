# Jadawel — جداول

Jadawel is an Arabic-first, RTL-native online spreadsheet-database: a spreadsheet and
relational database hybrid that lets a team structure, filter, link and share its data
without writing code.

It is built to be **self-hosted inside the Kingdom of Saudi Arabia**, so that customer
and citizen data never leaves the organisation's own infrastructure and deployments can
be brought in line with PDPL data-residency obligations.

## What makes it Arabic-first

- Arabic is the default UI locale — the interface ships in Arabic, not translated into
  it as an afterthought.
- `dir="rtl"` is applied at the document root; layout, grids, menus, forms and the
  frozen-column handles are all direction-aware.
- Styling uses CSS logical properties so LTR locales keep working unchanged. English,
  French, Dutch, German, Spanish, Italian, Polish, Korean and Ukrainian remain
  selectable per user.
- Arabic terminology is kept consistent through a project glossary
  (`docs/GLOSSARY_AR.md`).

## Tech stack

| Layer                  | Technology                                       |
| ---------------------- | ------------------------------------------------ |
| Backend                | Django 5.2, Django REST Framework, Python 3.14   |
| Async / scheduled work | Celery + Redis                                   |
| Database               | PostgreSQL (pgvector)                            |
| Frontend               | Nuxt 4, Vue 3, Vuex, Vite, SCSS                  |
| Tests                  | pytest / pytest-django, Vitest, Playwright (e2e) |
| Packaging              | `uv` (Python), `yarn` (Node 24), Docker          |

## Running the development stack

Everything is driven by [`just`](https://github.com/casey/just) from the repository
root. Run `just` to list every recipe, or `just help` for the getting-started guide.

### Option 1 — local processes (fastest hot reload)

Requires a local Python 3.14 and Node 24 toolchain. Postgres and Redis still run in
Docker.

```bash
just init          # install backend + frontend dependencies, create .env.local
just dev up        # start everything (Ctrl+C stops it again)
just dev up -d     # ...or start in the background
just dev stop      # stop background services
just dev logs      # tail the logs
```

### Option 2 — everything in Docker

```bash
just dc-dev build --parallel   # first time only
just dc-dev up -d
just dc-dev logs -f
just dc-dev down
```

Either way the app is served at **http://localhost:3000** and the API at
**http://localhost:8000**. Storybook runs on `:6006` and MailHog (captured dev email)
on `:8025`.

### Common tasks

```bash
just b migrate            # run Django migrations
just b test -n=auto       # backend pytest suite, in parallel
just f test               # frontend Vitest suite
just lint                 # backend + frontend linters
just fix                  # apply auto-fixes
just b <cmd> / just f <cmd>   # any other backend/frontend command
```

### Production images

Jadawel is not published to any container registry, so the production compose files
build from this repository:

```bash
just dc-prod build --parallel
just dc-prod up -d
```

`docker-compose.yml` (Caddy reverse proxy), `docker-compose.no-caddy.yml` (bring your
own proxy) and `docker-compose.all-in-one.yml` (single container) all build locally. A
Helm chart for Kubernetes lives in `deploy/helm/jadawel`.

## Repository layout

```
backend/            Django project (src/, tests/)
web-frontend/       Nuxt 4 application (modules/, server/, test/, stories/)
premium/            Paid-tier backend + web-frontend extensions
enterprise/         Enterprise-tier backend + web-frontend extensions
e2e-tests/          Playwright end-to-end suites
deploy/             Docker, Helm and reverse-proxy deployment recipes
docs/               Fork documentation (audit, Arabic glossary, RTL review, plans)
.agents/skills/     Reusable engineering workflows for this repository
```

`AGENTS.md` documents the coding standards, testing conventions and commit/PR
guidelines that apply here.

## Licence

Jadawel is a fork of Jadawel. The core is distributed under the MIT licence — see
`LICENSE`, whose copyright notice must be retained. Code under `premium/` and
`enterprise/` remains subject to its own licence terms.

## Security

Please report vulnerabilities privately — see `SECURITY.md`.
