# Repository Guidelines

Jadawel (جداول) is an Arabic-first, RTL-native spreadsheet-database forked from
Jadawel, self-hosted so that data stays inside Saudi Arabia. This repository is also
the CranL deployment copy, so it carries the root `Dockerfile` and
`.github/workflows/publish-image.yml` on top of the application.

**Pushing code does not change what is deployed.** The root `Dockerfile` pulls a
published image instead of building the monorepo, because the Nuxt production build
is OOM-killed on a 4 GB plan. Shipping is three steps: run the *Publish all-in-one
image* workflow, bump `ARG JADAWEL_IMAGE`, redeploy. `docs/DEPLOY_CRANL.md` holds
the procedure and `cranl_fix.md` the environment set that actually boots.

## Layout

```
backend/         Django project — src/jadawel (upstream), src/arabase (fork), tests/
web-frontend/    Nuxt 3 app — modules/{core,database,dashboard,…}, modules/arabase (fork)
website/         Static marketing pages
e2e-tests/       Playwright suites
embeddings/      Embedding sidecar, compose profile `ai`
deploy/          Docker, Helm and reverse-proxy recipes
docs/            Audit, Arabic glossary, RTL review, deployment write-ups
.agents/skills/  Reusable workflows for this repository
```

## Commands

`just` from the repository root wraps both halves. Run `just` for the recipe index.

```
just init          # install backend + frontend dependencies
just dev up        # local processes: app :3000, API :8000, Storybook :6006
just dc-dev up -d  # the same stack entirely in Docker
just b <cmd>       # backend/justfile      — b test -n=auto, b migrate, b lint
just f <cmd>       # web-frontend/justfile — f test, f lint
just lint | just fix | just test
```

Backend commands run through `uv`, frontend commands through `yarn` on Node 24.

## Arabic-first

- Arabic is the default locale and `dir="rtl"` is set at the document root. English,
  French, Dutch, German, Spanish, Italian, Polish, Korean and Ukrainian stay
  selectable per user, so both directions must keep working.
- Every user-facing string ships in `en.json` **and** `ar.json`. CI runs
  `yarn locale:check` in strict mode; one missing Arabic key fails the build.
- Take Arabic wording from `docs/GLOSSARY_AR.md`, and add a new recurring term there
  before using it. Keep placeholders (`{name}`, `@:action.save`), Latin technical
  tokens and Western digits (0–9) verbatim.
- Style with CSS logical properties (`margin-inline-start`, `inset-inline-end`).
  `csstools/use-logical` is a hard error under `web-frontend/modules/arabase/` and a
  warning elsewhere.

## Fork hygiene

- `premium/` and `enterprise/` are deleted for licence reasons.
  `backend/tests/arabase/test_fork_hygiene.py` fails if `baserow_premium` or
  `baserow_enterprise` becomes importable, or if `JADAWEL_OSS_ONLY` stops being true.
  Run it after every upstream merge.
- Fork features are **additive**: they live in `backend/src/arabase/` and
  `web-frontend/modules/arabase/`. The backend hooks into Jadawel's registries from
  `ArabaseConfig.ready()`, and its API mounts under `/api/arabase/` through
  `ArabasePlugin`, so a new feature needs no core edit.
- Editing an upstream-derived core file under `backend/src/jadawel/` is the last
  resort, and every such edit is logged in `PATCHES.md` with its reason. Files you
  create under `arabase/`, `docs/` or `.github/` are additive and stay out of that log.
- The code is named `jadawel` throughout, with no compatibility aliases left in the
  source: the Python distribution, the `jadawel.*` import namespace, `src/jadawel`,
  the `@jadawel` frontend alias, `JADAWEL_*` environment variables, `/jadawel` image
  paths, Celery task names, OpenTelemetry metric names, the `local_jadawel` service
  types and `LocalJadawel*` tables, `templates/jadawel`, the Postgres role, the
  `jadawel_template_version` key and every bundled template's sample data, the
  `X-Jadawel-*` webhook headers and the `Jadawel-View-Authorization` header.
- Four things still read `baserow` **on purpose**, and renaming any of them is a bug:
  1. The `Baserow B.V.` copyright, plus the Jack Linke and Tal Shprecher notices.
     MIT terminates the grant if the notice is dropped, so `test_fork_hygiene.py`
     asserts each one. **Never rewrite an upstream author's name.**
  2. Upstream's Docker images, issue URLs and the fork's own provenance line.
  3. `baserow_premium` / `baserow_enterprise` — upstream's real package names, which
     `test_fork_hygiene.py` asserts are *not* importable.
  4. Historical migration filenames and their `CreateModel`/dependency strings, which
     later `RenameModel` operations refer to by name.
  `DatabaseRow*` contains the substring `baserow`; a case-insensitive rename will
  corrupt it. `docs/RENAME_TO_JADAWEL.md` records how the rename was carried out.

## Coding style

Python 3.14, 4-space indentation, Ruff (`ruff check`, `ruff format`) at 88 columns,
with `jadawel` and `arabase` both first-party for isort. Name tests `test_*.py`.

Vue 3 and Nuxt 3 with ESLint, Stylelint and Prettier. SCSS class names follow the BEM
pattern Stylelint enforces. Render functions use Vue 3 semantics — import `h` from
`vue`. A file containing JSX needs a `.jsx` or `.tsx` extension so Vite parses it.

## Testing

`just b test -n=auto` runs pytest with pytest-django, `just f test` runs Vitest, and
browser flows live in `e2e-tests/`. Add backend tests for backend changes and targeted
frontend tests for component or store behaviour.

`.github/workflows/jadawel-ci.yml` gates a pull request on six jobs. Two are
fork-specific and easy to miss locally — Arabic locale parity (`yarn locale:check`)
and fork hygiene (`pytest tests/arabase -q`). Run both before pushing.

## Commits and pull requests

Branch from `main`; history is linear, so rebase rather than merge. Subjects are
short, imperative Conventional Commits — `feat(dashboard):`, `fix(mcp):`,
`chore(deploy):`. This fork keeps no changelog directory; record deployment findings
and audits as documents in `docs/` instead. Call out schema or environment changes,
and attach screenshots for UI work.

## Skills

`.agents/skills/` is canonical. `.claude/skills` is a symlink to it that a Windows
checkout leaves as a plain text file, so read through `.agents/skills/`.

| Skill | When to use |
|---|---|
| `add-django-config-env-var` | Adding a Django setting backed by an env var and propagating it to `base.py`, the compose files, `env-remap.mjs` and `docs/CONFIGURATION.md` |
| `create-in-app-notification` | Adding a `NotificationType` with its frontend rendering, target routing and duplicate prevention |
| `create-update-service` | Creating or updating an integration type or service type in `contrib/integrations` |
| `silk-profiler` | Investigating a slow endpoint, an N+1 query or a request's query pattern with Django Silk |
| `write-backend-unit-test` | Writing pytest tests with the repository's DRF `APIClient` and fixture patterns |
| `write-frontend-unit-test` | Writing Vitest tests with the repository's `TestApp`, Vue Test Utils and snapshot patterns |

## Security and configuration

Keep secrets out of the tree: `.env.local` for local processes, `.env.docker-dev` for
Docker, and the deploy configs for production. Report vulnerabilities privately
through the contact path in `SECURITY.md`.

<!-- graft:start -->
## Graft — repo context graph

This repo is indexed in `graft/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `graft map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `graft ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `graft grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `graft skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `graft callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `graft/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `graft ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `graft build` (deterministic,
no API key, $0).
<!-- graft:end -->
